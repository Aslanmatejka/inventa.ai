import { useCallback, useRef } from 'react';
import { useAppContext } from '../context/AppContext';
import { buildProductStream, rebuildWithParameters, saveMessage, getProject, askStream, planStream, cancelBuild, authFetch } from '../api';
import { API_HOST } from '../config';

// Map SSE steps to progress percentage
const STEP_PROGRESS = { 1: 10, 2: 40, 2.5: 50, 3: 55, 3.5: 65, 4: 75, 4.5: 80, 5: 90, 6: 100 };

export function useBuild() {
  const { state, dispatch } = useAppContext();

  // selectedModel is stored in App-level state and passed via AppContext
  const selectedModel = state.selectedModel || '';

  // AbortController ref for cancelling in-progress builds
  const abortRef = useRef(null);

  const initializeScene = useCallback(async () => {
    try {
      const response = await authFetch(`${API_HOST}/api/scene/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Workspace ' + new Date().toLocaleDateString() }),
      });
      const data = await response.json();
      if (data.success) {
        dispatch({ type: 'SET_SCENE', payload: data.scene });
        return data.scene;
      }
    } catch (error) {
      console.error('Scene initialization failed:', error);
    }
    return null;
  }, [dispatch]);

  const resolveStlUrl = useCallback((buildResult) => {
    let stlFile = null;

    // Check buildResult.files.cad structure
    if (buildResult.files?.cad?.files) {
      const cadFiles = buildResult.files.cad.files;
      if (typeof cadFiles === 'string') {
        stlFile = cadFiles.endsWith('.stl') ? cadFiles : null;
      } else if (typeof cadFiles === 'object' && cadFiles.stl) {
        stlFile = cadFiles.stl;
      } else if (Array.isArray(cadFiles)) {
        stlFile = cadFiles.find(f => f.endsWith('.stl'));
      }
    }

    // Fallback to legacy structure
    if (!stlFile && buildResult.files?.stl) {
      stlFile = buildResult.files.stl;
    } else if (!stlFile && buildResult.files && Array.isArray(buildResult.files)) {
      const firstPart = buildResult.files[0];
      if (firstPart?.files) {
        if (typeof firstPart.files === 'object' && !Array.isArray(firstPart.files) && firstPart.files.stl) {
          stlFile = firstPart.files.stl;
        } else if (Array.isArray(firstPart.files)) {
          stlFile = firstPart.files.find(f => f.endsWith('.stl'));
        }
      }
    }

    // Fallback to top-level stlUrl
    if (!stlFile && buildResult.stlUrl) {
      stlFile = buildResult.stlUrl;
    }

    if (!stlFile) return null;
    const stlPath = stlFile.startsWith('/') ? stlFile : `/exports/cad/${stlFile}`;
    return `${API_HOST}${stlPath}`;
  }, []);

  const addProductToScene = useCallback(async (buildResult, isModification = false) => {
    let scene = state.currentScene;
    if (!scene) {
      scene = await initializeScene();
    }

    // Helper: add a single product to the scene with local fallback
    const doAddProduct = async (bResult, stlUrlValue, isMod, sceneObj) => {
      let productPosition = { x: 0, y: 0, z: 0 };
      if (isMod && state.sceneProducts.length > 0) {
        const lastProduct = state.sceneProducts[state.sceneProducts.length - 1];
        productPosition = lastProduct.position || { x: 0, y: 0, z: 0 };
      } else if (!isMod) {
        productPosition = { x: state.sceneProducts.length * 100, y: 0, z: 0 };
      }

      const newProduct = {
        instanceId: `${bResult.buildId}_${Date.now()}`,
        buildId: bResult.buildId,
        instanceName: bResult.design?.product_type || 'Product',
        position: productPosition,
        rotation: { x: 0, y: 0, z: 0 },
        scale: { x: 1, y: 1, z: 1 },
        stlUrl: stlUrlValue,
        productType: bResult.design?.product_type,
        designData: bResult.design,
      };

      // Try scene API, but always add the product locally even if API fails
      if (sceneObj) {
        try {
          const response = await authFetch(`${API_HOST}/api/scene/${sceneObj.sceneId}/add-product`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              buildId: bResult.buildId,
              instanceName: newProduct.instanceName,
              position: productPosition,
              rotation: { x: 0, y: 0, z: 0 },
              scale: { x: 1, y: 1, z: 1 },
            }),
          });
          if (response.ok) {
            const data = await response.json();
            if (data.success && data.product) {
              newProduct.instanceId = data.product.instanceId;
              newProduct.instanceName = data.product.instanceName;
              newProduct.position = data.product.position;
              newProduct.rotation = data.product.rotation;
              newProduct.scale = data.product.scale;
            }
          }
        } catch (sceneErr) {
          console.warn('Scene API failed, using local product data:', sceneErr);
        }
      }

      // Always dispatch — ensures product renders even if scene API fails
      if (isMod) {
        dispatch({ type: 'REPLACE_LAST_PRODUCT', payload: newProduct });
      } else {
        dispatch({ type: 'ADD_PRODUCT', payload: newProduct });
      }
    };

    // Resolve STL URL first — used by both assembly and single-part paths
    const stlUrl = resolveStlUrl(buildResult);

    // Handle assembly parts
    if (buildResult.isAssembly && Array.isArray(buildResult.files) && buildResult.files.length > 1) {
      const addedProducts = [];
      for (let i = 0; i < buildResult.files.length; i++) {
        const part = buildResult.files[i];
        let stlFile = null;
        if (part.files) {
          if (typeof part.files === 'object' && !Array.isArray(part.files) && part.files.stl) {
            stlFile = part.files.stl;
          } else if (Array.isArray(part.files)) {
            stlFile = part.files.find(f => f.endsWith('.stl'));
          }
        }
        if (!stlFile) continue;
        const stlPath = stlFile.startsWith('/') ? stlFile : `/exports/cad/${stlFile}`;
        const partProduct = {
          instanceId: `${buildResult.buildId}_part${i + 1}_${Date.now()}`,
          buildId: buildResult.buildId + `_part${i + 1}`,
          instanceName: part.partName || `Part ${i + 1}`,
          position: { x: i * 50, y: 0, z: 0 },
          rotation: { x: 0, y: 0, z: 0 },
          scale: { x: 1, y: 1, z: 1 },
          stlUrl: `${API_HOST}${stlPath}`,
          productType: part.partName,
          designData: buildResult.design,
        };

        if (scene) {
          try {
            const response = await authFetch(`${API_HOST}/api/scene/${scene.sceneId}/add-product`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                buildId: partProduct.buildId,
                instanceName: partProduct.instanceName,
                position: partProduct.position,
                rotation: partProduct.rotation,
                scale: partProduct.scale,
              }),
            });
            if (response.ok) {
              const data = await response.json();
              if (data.success && data.product) {
                partProduct.instanceId = data.product.instanceId;
                partProduct.position = data.product.position;
                partProduct.rotation = data.product.rotation;
                partProduct.scale = data.product.scale;
              }
            }
          } catch (sceneErr) {
            console.warn('Scene API failed for assembly part, using local fallback:', sceneErr);
          }
        }
        addedProducts.push(partProduct);
      }
      if (addedProducts.length > 0) {
        if (isModification) {
          dispatch({ type: 'REPLACE_ALL_PRODUCTS', payload: addedProducts });
        } else {
          dispatch({ type: 'ADD_PRODUCTS', payload: addedProducts });
        }
      }
      return;
    }

    // Single-part design — must have STL URL
    if (!stlUrl) {
      // Last resort: construct from buildId
      const fallbackUrl = buildResult.buildId
        ? `${API_HOST}/exports/cad/${buildResult.buildId}.stl`
        : null;
      if (!fallbackUrl) {
        console.error('No STL file found in build result:', Object.keys(buildResult));
        return;
      }
      console.warn('resolveStlUrl returned null — using buildId fallback:', fallbackUrl);
      return doAddProduct(buildResult, fallbackUrl, isModification, scene);
    }

    return doAddProduct(buildResult, stlUrl, isModification, scene);
  }, [state.currentScene, state.sceneProducts, dispatch, initializeScene, resolveStlUrl]);

  const handleBuild = useCallback(async (prompt, image = null) => {
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: prompt,
      timestamp: new Date(),
    };
    dispatch({ type: 'ADD_MESSAGE', payload: userMessage });

    // ── Ask mode: text-only Q&A, no CAD build ──
    if (state.interactionMode === 'ask') {
      const thinkingMsg = {
        id: Date.now() + 1,
        type: 'assistant',
        status: 'building',
        content: 'Thinking...',
        timestamp: new Date(),
      };
      dispatch({ type: 'ADD_MESSAGE', payload: thinkingMsg });
      dispatch({ type: 'BUILD_START' });
      try {
        const answer = await askStream(prompt, state.currentDesign, selectedModel);
        dispatch({ type: 'BUILD_COMPLETE', payload: { result: null } });
        dispatch({
          type: 'UPDATE_LAST_MESSAGE',
          payload: { status: 'success', content: answer.message, responseType: 'ask' },
        });
      } catch (err) {
        dispatch({ type: 'BUILD_ERROR' });
        dispatch({ type: 'UPDATE_LAST_MESSAGE', payload: { status: 'error', content: err.message } });
      }
      return;
    }

    // ── Plan mode: structured multi-step build plan ──
    if (state.interactionMode === 'plan') {
      const thinkingMsg = {
        id: Date.now() + 1,
        type: 'assistant',
        status: 'building',
        content: 'Creating build plan...',
        timestamp: new Date(),
      };
      dispatch({ type: 'ADD_MESSAGE', payload: thinkingMsg });
      dispatch({ type: 'BUILD_START' });
      try {
        const result = await planStream(prompt, state.currentDesign, selectedModel);
        dispatch({ type: 'BUILD_COMPLETE', payload: { result: null } });
        dispatch({
          type: 'UPDATE_LAST_MESSAGE',
          payload: {
            status: 'success',
            content: result.message || 'Build plan ready',
            plan: result.plan || null,
            responseType: 'plan',
          },
        });
      } catch (err) {
        dispatch({ type: 'BUILD_ERROR' });
        dispatch({ type: 'UPDATE_LAST_MESSAGE', payload: { status: 'error', content: err.message } });
      }
      return;
    }

    // ── Agent mode (default): full CAD build pipeline ──
    // If there's an uploaded file with editable solid geometry, use NLP edit flow
    const uploaded = state.uploadedFile;
    const useNLPEdit = uploaded && uploaded.editable && uploaded.importCode;

    const isModification = (state.currentDesign && state.currentDesign.code) || useNLPEdit;
    const buildingMessage = {
      id: Date.now() + 1,
      type: 'assistant',
      status: 'building',
      content: useNLPEdit
        ? `Editing ${uploaded.filename} with AI...`
        : isModification
          ? 'Modifying your existing design...'
          : 'Let me design that for you...',
      steps: [],
      healingLog: [],
      timestamp: new Date(),
    };
    dispatch({ type: 'ADD_MESSAGE', payload: buildingMessage });
    dispatch({ type: 'BUILD_START' });

    // Create AbortController for this build
    const controller = new AbortController();
    abortRef.current = controller;

    // Common onStep callback that captures streamBuildId
    const onStepHandler = (stepData) => {
      if (stepData.streamBuildId) {
        dispatch({ type: 'SET_STREAM_BUILD_ID', payload: stepData.streamBuildId });
      }
      if (stepData.status === 'cancelled') {
        dispatch({ type: 'BUILD_CANCELLED' });
        dispatch({ type: 'UPDATE_LAST_MESSAGE', payload: { status: 'info', content: 'Build cancelled.' } });
        return;
      }
      dispatch({ type: 'UPDATE_BUILD_STEP', payload: { stepData } });
      if (stepData.step && STEP_PROGRESS[stepData.step]) {
        dispatch({ type: 'BUILD_PROGRESS', payload: STEP_PROGRESS[stepData.step] });
      }
    };

    // ── NLP Edit flow for uploaded files: route through streaming pipeline ──
    if (useNLPEdit) {
      try {
        // Build a previousDesign with the import code so the streaming
        // endpoint treats this as a modification (triggering the lightweight
        // edit system prompt on the backend = ~2K tokens vs ~35K).
        const previousDesign = {
          code: state.currentDesign?.code || uploaded.importCode,
          parameters: state.currentDesign?.parameters || [],
          explanation: state.currentDesign?.explanation || {},
        };

        const buildResult = await buildProductStream(
          prompt,
          previousDesign,
          onStepHandler,
          state.currentProjectId,
          selectedModel,
          controller.signal,
          image
        );

        // Graceful cancellation / timeout — onStepHandler already dispatched BUILD_CANCELLED.
        if (!buildResult) return;

        dispatch({ type: 'BUILD_COMPLETE', payload: { result: buildResult } });
        {
          let msg = buildResult.reasoning || 'Edit applied!';
          if (buildResult.healingWarning) {
            msg += '\n\n⚠️ ' + buildResult.healingWarning;
          }
          if (buildResult.tokens && (buildResult.tokens.input || buildResult.tokens.output)) {
            const t = buildResult.tokens;
            const cost = t.costUsd ? ` · $${Number(t.costUsd).toFixed(4)}` : '';
            msg += `\n\n🪙 Tokens: ${t.input.toLocaleString()} in / ${t.output.toLocaleString()} out${cost}`;
          }
          dispatch({
            type: 'UPDATE_LAST_MESSAGE',
            payload: {
              status: buildResult.healingWarning ? 'warning' : 'success',
              content: msg,
              result: buildResult,
            },
          });
        }

        // Save project tracking and chat messages (same as standard flow)
        if (buildResult.projectId) {
          dispatch({ type: 'SET_PROJECT_ID', payload: buildResult.projectId });
          try {
            await saveMessage(buildResult.projectId, 'user', prompt);
            await saveMessage(
              buildResult.projectId,
              'assistant',
              buildResult.explanation?.design_intent || 'Design edited',
              buildResult,
              'success'
            );
          } catch (msgErr) {
            console.warn('Failed to save chat messages:', msgErr);
          }
        }

        // Update uploaded file for chained edits
        if (buildResult.design?.code) {
          dispatch({
            type: 'SET_UPLOADED_FILE',
            payload: { ...uploaded, importCode: buildResult.design.code, buildId: buildResult.buildId },
          });
        }

        await addProductToScene(buildResult, true);
      } catch (err) {
        if (err.name === 'AbortError') {
          dispatch({ type: 'BUILD_CANCELLED' });
          dispatch({ type: 'UPDATE_LAST_MESSAGE', payload: { status: 'info', content: 'Build cancelled.' } });
        } else {
          dispatch({ type: 'BUILD_ERROR' });
          dispatch({ type: 'UPDATE_LAST_MESSAGE', payload: { status: 'error', content: err.message } });
        }
      } finally {
        abortRef.current = null;
      }
      return;
    }

    // ── Standard build flow ──
    try {
      const buildResult = await buildProductStream(
        prompt,
        state.currentDesign,
        onStepHandler,
        state.currentProjectId,
        selectedModel,
        controller.signal,
        image
      );

      // Graceful cancellation / timeout — onStepHandler already dispatched BUILD_CANCELLED.
      if (!buildResult) return;

      dispatch({ type: 'BUILD_COMPLETE', payload: { result: buildResult } });

      {
        let msg = buildResult.reasoning || "Here's your design!";
        if (buildResult.healingWarning) {
          msg += '\n\n⚠️ ' + buildResult.healingWarning;
        }
        if (buildResult.tokens && (buildResult.tokens.input || buildResult.tokens.output)) {
          const t = buildResult.tokens;
          const cost = t.costUsd ? ` · $${Number(t.costUsd).toFixed(4)}` : '';
          msg += `\n\n🪙 Tokens: ${t.input.toLocaleString()} in / ${t.output.toLocaleString()} out${cost}`;
        }
        dispatch({
          type: 'UPDATE_LAST_MESSAGE',
          payload: {
            status: buildResult.healingWarning ? 'warning' : 'success',
            content: msg,
            result: buildResult,
          },
        });
      }

      // Save chat messages to DB (fire-and-forget)
      if (buildResult.projectId) {
        dispatch({ type: 'SET_PROJECT_ID', payload: buildResult.projectId });
        try {
          await saveMessage(buildResult.projectId, 'user', prompt);
          await saveMessage(
            buildResult.projectId,
            'assistant',
            buildResult.explanation?.design_intent || 'Design created',
            buildResult,
            'success'
          );
        } catch (msgErr) {
          console.warn('Failed to save chat messages:', msgErr);
        }
      }

      await addProductToScene(buildResult, !!isModification);
    } catch (err) {
      if (err.name === 'AbortError') {
        dispatch({ type: 'BUILD_CANCELLED' });
        dispatch({ type: 'UPDATE_LAST_MESSAGE', payload: { status: 'info', content: 'Build cancelled.' } });
      } else {
        dispatch({ type: 'BUILD_ERROR' });
        dispatch({
          type: 'UPDATE_LAST_MESSAGE',
          payload: { status: 'error', content: err.message },
        });
      }
    } finally {
      abortRef.current = null;
    }
  }, [state.currentDesign, state.currentProjectId, state.uploadedFile, state.interactionMode, selectedModel, dispatch, addProductToScene]);

  const handleRebuild = useCallback(async (paramValues) => {
    if (!state.currentBuildId) return;
    try {
      const result = await rebuildWithParameters(state.currentBuildId, paramValues);
      if (result.success) {
        // Build a result object and replace the product
        const stlPath = result.stlUrl || result.files?.stl;
        if (stlPath) {
          const fullUrl = stlPath.startsWith('http') ? stlPath : `${API_HOST}${stlPath}`;
          const updatedProduct = {
            ...state.sceneProducts[state.sceneProducts.length - 1],
            stlUrl: fullUrl + '?t=' + Date.now(), // cache-bust
          };
          dispatch({ type: 'REPLACE_LAST_PRODUCT', payload: updatedProduct });
        }
      }
      return result;
    } catch (error) {
      console.error('Rebuild failed:', error);
      throw error;
    }
  }, [state.currentBuildId, state.sceneProducts, dispatch]);

  const handleProjectSelect = useCallback(async (project) => {
    try {
      const data = await getProject(project.id);
      if (!data.success || !data.project) return;
      const proj = data.project;
      dispatch({ type: 'SET_PROJECT_ID', payload: proj.id });

      if (proj.messages && proj.messages.length > 0) {
        const restoredMessages = proj.messages.map((msg, idx) => ({
          id: Date.now() + idx,
          type: msg.role,
          content: msg.content,
          status: msg.status || (msg.role === 'assistant' ? 'success' : undefined),
          result: msg.build_result || undefined,
          timestamp: new Date(msg.created_at),
        }));
        dispatch({ type: 'SET_MESSAGES', payload: restoredMessages });
      } else {
        dispatch({ type: 'SET_MESSAGES', payload: [] });
      }

      if (proj.builds && proj.builds.length > 0) {
        const lastBuild = proj.builds[proj.builds.length - 1];
        dispatch({
          type: 'SET_DESIGN',
          payload: {
            code: lastBuild.code,
            parameters: lastBuild.parameters,
            explanation: lastBuild.explanation,
          },
        });
        dispatch({ type: 'SET_BUILD_ID', payload: lastBuild.build_id });

        if (lastBuild.stl_path) {
          const buildResult = {
            buildId: lastBuild.build_id,
            stlUrl: lastBuild.stl_path,
            design: {
              code: lastBuild.code,
              parameters: lastBuild.parameters,
              explanation: lastBuild.explanation,
            },
          };
          await addProductToScene(buildResult);
        }
      } else {
        dispatch({ type: 'SET_DESIGN', payload: null });
        dispatch({ type: 'SET_BUILD_ID', payload: null });
      }
    } catch (error) {
      console.error('Failed to load project:', error);
    }
  }, [dispatch, addProductToScene]);

  const handleNewProject = useCallback(() => {
    dispatch({ type: 'SET_SHOW_PROJECT_BROWSER', payload: false });
    dispatch({ type: 'SET_MESSAGES', payload: [] });
    dispatch({ type: 'SET_DESIGN', payload: null });
    dispatch({ type: 'SET_PROJECT_ID', payload: null });
    dispatch({ type: 'SET_BUILD_ID', payload: null });
    dispatch({ type: 'SET_RESULT', payload: null });
    dispatch({ type: 'SET_STATUS', payload: 'idle' });
    dispatch({ type: 'SET_SCENE_PRODUCTS', payload: [] });
    dispatch({ type: 'SET_SCENE', payload: null });
    dispatch({ type: 'SET_UPLOADED_FILE', payload: null });
    initializeScene();
  }, [dispatch, initializeScene]);

  // ── File Upload handler ──────────────────────────────────────────────
  const handleUploadComplete = useCallback(async (uploadResult) => {
    // uploadResult comes from the /api/upload response
    const stlUrl = uploadResult.stlFile
      ? `${API_HOST}${uploadResult.stlFile}`
      : null;

    // Store uploaded file metadata for NLP editing
    dispatch({
      type: 'SET_UPLOADED_FILE',
      payload: {
        buildId: uploadResult.buildId,
        filename: uploadResult.originalFilename,
        importCode: uploadResult.importCode,
        editable: uploadResult.editable,
        boundingBox: uploadResult.boundingBox,
        geometryInfo: uploadResult.geometryInfo,
        format: uploadResult.format,
        stlUrl,
        stepUrl: uploadResult.stepFile ? `${API_HOST}${uploadResult.stepFile}` : null,
      },
    });

    // Set as current design so NLP edits use the import code
    if (uploadResult.importCode) {
      dispatch({
        type: 'SET_DESIGN',
        payload: {
          code: uploadResult.importCode,
          parameters: [],
          explanation: {
            design_intent: `Imported ${uploadResult.originalFilename} (${uploadResult.format})`,
          },
        },
      });
    }

    // Set build ID for exports
    dispatch({ type: 'SET_BUILD_ID', payload: uploadResult.buildId });

    // Set result for export panel
    dispatch({
      type: 'SET_RESULT',
      payload: {
        buildId: uploadResult.buildId,
        stlUrl: uploadResult.stlFile,
        stepUrl: uploadResult.stepFile,
      },
    });
    dispatch({ type: 'SET_STATUS', payload: 'success' });

    // Build geometry info message
    const bb = uploadResult.boundingBox || {};
    const gi = uploadResult.geometryInfo || {};
    let infoLines = [`**${uploadResult.originalFilename}** imported successfully!`];
    if (bb.width) infoLines.push(`📐 Size: ${bb.width} × ${bb.depth} × ${bb.height} mm`);
    if (gi.faces) infoLines.push(`🔷 Geometry: ${gi.faces} faces, ${gi.edges || gi.vertices || '?'} edges`);
    if (gi.volume) infoLines.push(`📦 Volume: ${gi.volume.toLocaleString()} mm³`);
    if (uploadResult.editable) {
      infoLines.push(`\n✅ **Full NLP editing supported** — describe changes in the chat to modify this model.`);
    } else {
      infoLines.push(`\n⚠️ Mesh file — view & export supported. For full NLP editing, upload a STEP or IGES file.`);
    }

    dispatch({
      type: 'ADD_MESSAGE',
      payload: {
        id: Date.now(),
        type: 'assistant',
        status: 'success',
        content: infoLines.join('\n'),
        result: {
          buildId: uploadResult.buildId,
          stlUrl: uploadResult.stlFile,
          stepUrl: uploadResult.stepFile,
        },
        timestamp: new Date(),
      },
    });

    // Add to 3D scene
    await addProductToScene({
      buildId: uploadResult.buildId,
      stlUrl: uploadResult.stlFile,
      design: { product_type: uploadResult.originalFilename },
    });
  }, [dispatch, addProductToScene]);

  // ── Stop / Cancel in-progress build ──
  const handleStopBuild = useCallback(async () => {
    // Abort the fetch stream on the frontend
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    // Also signal the backend to stop
    if (state.streamBuildId) {
      try { await cancelBuild(state.streamBuildId); } catch { /* best-effort */ }
    }
    dispatch({ type: 'BUILD_CANCELLED' });
    dispatch({ type: 'UPDATE_LAST_MESSAGE', payload: { status: 'info', content: 'Build cancelled by user.' } });
  }, [state.streamBuildId, dispatch]);

  return {
    handleBuild,
    handleRebuild,
    handleStopBuild,
    handleProjectSelect,
    handleNewProject,
    initializeScene,
    addProductToScene,
    handleUploadComplete,
  };
}
