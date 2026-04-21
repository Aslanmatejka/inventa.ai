"""
Supabase Database Service for Product Builder
Handles persistent storage of projects, builds, chat history, and version history.
Uses the Supabase Python client (REST API) for reliable connectivity.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from supabase import create_client, Client


class DatabaseService:
    """Supabase database service using the official Python client (PostgREST)."""

    def __init__(self):
        self.client: Optional[Client] = None
        self._initialized = False

    def initialize(self, supabase_url: str, supabase_key: str):
        """Initialize Supabase client and verify connection."""
        self.client = create_client(supabase_url, supabase_key)

        # Verify connection by querying projects table
        self.client.table("projects").select("id").limit(1).execute()

        self._initialized = True
        print("✅ Supabase database initialized successfully")

    @property
    def is_available(self) -> bool:
        return self._initialized

    def _check(self):
        if not self._initialized:
            raise RuntimeError("Database not initialized. Call initialize() first.")

    # ── Project CRUD ────────────────────────────────────────────────────

    def create_project(self, name: str = "Untitled Project", description: str = None, user_id: str = None) -> Dict[str, Any]:
        self._check()
        data = {"name": name}
        if description:
            data["description"] = description
        if user_id:
            data["user_id"] = user_id
        result = self.client.table("projects").insert(data).execute()
        return self._project_to_dict(result.data[0])

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        self._check()
        result = self.client.table("projects").select("*").eq("id", project_id).execute()
        if not result.data:
            return None
        project = result.data[0]

        # Fetch related builds and messages
        builds = self.client.table("builds").select("*").eq("project_id", project_id).order("created_at").execute()
        messages = self.client.table("chat_messages").select("*").eq("project_id", project_id).order("created_at").execute()

        d = self._project_to_dict(project)
        d["builds"] = [self._build_to_dict(b) for b in builds.data]
        d["messages"] = [self._message_to_dict(m) for m in messages.data]
        d["build_count"] = len(builds.data)
        if builds.data:
            d["last_prompt"] = builds.data[-1].get("prompt")
            d["last_build_id"] = builds.data[-1].get("build_id")
        return d

    def list_projects(self, user_id: str = None) -> List[Dict[str, Any]]:
        self._check()
        if not user_id:
            return []
        query = self.client.table("projects").select("*").eq("user_id", user_id)
        result = query.order("updated_at", desc=True).execute()
        projects = []
        for p in result.data:
            builds = self.client.table("builds").select("id,prompt,build_id").eq("project_id", p["id"]).order("created_at").execute()
            d = self._project_to_dict(p)
            d["build_count"] = len(builds.data)
            if builds.data:
                d["last_prompt"] = builds.data[-1].get("prompt")
                d["last_build_id"] = builds.data[-1].get("build_id")
            projects.append(d)
        return projects

    def update_project(self, project_id: str, name: str = None, description: str = None) -> Optional[Dict[str, Any]]:
        self._check()
        data = {"updated_at": datetime.now(timezone.utc).isoformat()}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        result = self.client.table("projects").update(data).eq("id", project_id).execute()
        if not result.data:
            return None
        return self._project_to_dict(result.data[0])

    def delete_project(self, project_id: str) -> bool:
        self._check()
        result = self.client.table("projects").delete().eq("id", project_id).execute()
        return len(result.data) > 0

    # ── Build CRUD ──────────────────────────────────────────────────────

    def save_build(self, project_id: str, build_id: str, prompt: str, code: str = None,
                   parameters: list = None, explanation: dict = None, stl_path: str = None,
                   step_path: str = None, script_path: str = None, is_modification: bool = False) -> Dict[str, Any]:
        self._check()
        data = {
            "project_id": project_id,
            "build_id": build_id,
            "prompt": prompt,
            "code": code,
            "parameters": parameters,
            "explanation": explanation,
            "stl_path": stl_path,
            "step_path": step_path,
            "script_path": script_path,
            "is_modification": is_modification,
        }
        result = self.client.table("builds").insert(data).execute()

        # Touch parent project
        self.client.table("projects").update(
            {"updated_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", project_id).execute()

        return self._build_to_dict(result.data[0])

    def get_builds_for_project(self, project_id: str) -> List[Dict[str, Any]]:
        self._check()
        result = self.client.table("builds").select("*").eq("project_id", project_id).order("created_at").execute()
        return [self._build_to_dict(b) for b in result.data]

    def get_all_builds(self, limit: int = 50) -> List[Dict[str, Any]]:
        self._check()
        result = self.client.table("builds").select("*").order("created_at", desc=True).limit(limit).execute()
        return [self._build_to_dict(b) for b in result.data]

    def get_project_history_for_ai(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Fetch concise project history for AI context.
        
        Returns the project name, chronological list of prompts,
        and the latest build's code/parameters — enough for the AI
        to understand the design evolution without sending megabytes.
        """
        self._check()
        try:
            project = self.client.table("projects").select("id,name").eq("id", project_id).execute()
            if not project.data:
                return None

            builds = (self.client.table("builds")
                      .select("prompt,is_modification,code,parameters,explanation,created_at")
                      .eq("project_id", project_id)
                      .order("created_at")
                      .execute())

            if not builds.data:
                return None

            # Build a concise history: just prompts + modification flag
            history = []
            for b in builds.data:
                history.append({
                    "prompt": b.get("prompt", ""),
                    "is_modification": b.get("is_modification", False),
                })

            # Latest build has full code context
            latest = builds.data[-1]

            return {
                "project_name": project.data[0].get("name", "Untitled"),
                "build_count": len(builds.data),
                "history": history,
                "latest_code": latest.get("code"),
                "latest_parameters": latest.get("parameters"),
                "latest_explanation": latest.get("explanation"),
            }
        except Exception as e:
            print(f"⚠️ Failed to fetch project history: {e}")
            return None

    # ── Chat Message CRUD ───────────────────────────────────────────────

    def save_chat_message(self, project_id: str, role: str, content: str,
                          build_result: dict = None, status: str = None) -> Dict[str, Any]:
        self._check()
        data = {
            "project_id": project_id,
            "role": role,
            "content": content,
            "build_result": build_result,
            "status": status,
        }
        result = self.client.table("chat_messages").insert(data).execute()

        # Touch parent project
        self.client.table("projects").update(
            {"updated_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", project_id).execute()

        return self._message_to_dict(result.data[0])

    def get_messages_for_project(self, project_id: str) -> List[Dict[str, Any]]:
        self._check()
        result = self.client.table("chat_messages").select("*").eq("project_id", project_id).order("created_at").execute()
        return [self._message_to_dict(m) for m in result.data]

    # ── Version History CRUD ────────────────────────────────────────────

    def save_version(self, build_id: str, label: str = "Snapshot", code: str = None,
                     parameters: list = None, explanation: dict = None, prompt: str = None) -> Dict[str, Any]:
        self._check()
        data = {
            "build_id": build_id,
            "label": label,
            "code": code,
            "parameters": parameters,
            "explanation": explanation,
            "prompt": prompt,
        }
        result = self.client.table("version_history").insert(data).execute()
        return self._version_to_dict(result.data[0])

    def list_versions(self, build_id: str) -> List[Dict[str, Any]]:
        self._check()
        result = self.client.table("version_history").select("*").eq("build_id", build_id).order("created_at", desc=True).execute()
        return [self._version_to_dict(v) for v in result.data]

    def get_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        self._check()
        result = self.client.table("version_history").select("*").eq("id", version_id).execute()
        if not result.data:
            return None
        return self._version_to_dict(result.data[0])

    # ── Scene CRUD ──────────────────────────────────────────────────────

    def create_scene(self, name: str = "Default Scene", project_id: str = None) -> Dict[str, Any]:
        self._check()
        data = {"name": name}
        if project_id:
            data["project_id"] = project_id
        result = self.client.table("scenes").insert(data).execute()
        row = result.data[0]
        return self._scene_to_dict(row)

    def get_scene(self, scene_id: str) -> Optional[Dict[str, Any]]:
        self._check()
        result = self.client.table("scenes").select("*").eq("id", scene_id).execute()
        if not result.data:
            return None
        scene = self._scene_to_dict(result.data[0])
        # Fetch products
        products = self.client.table("scene_products").select("*").eq("scene_id", scene_id).order("created_at").execute()
        scene["products"] = [self._scene_product_to_dict(p) for p in products.data]
        return scene

    def add_scene_product(self, scene_id: str, product: dict) -> Dict[str, Any]:
        self._check()
        data = {
            "scene_id": scene_id,
            "instance_id": product.get("instanceId", str(uuid.uuid4())),
            "build_id": product.get("buildId", ""),
            "instance_name": product.get("instanceName", ""),
            "stl_url": product.get("stlUrl", ""),
            "product_type": product.get("productType", ""),
            "position": product.get("position", {"x": 0, "y": 0, "z": 0}),
            "rotation": product.get("rotation", {"x": 0, "y": 0, "z": 0}),
            "scale": product.get("scale", {"x": 1, "y": 1, "z": 1}),
            "design_data": product.get("designData"),
        }
        result = self.client.table("scene_products").insert(data).execute()
        return self._scene_product_to_dict(result.data[0])

    def update_scene_product_transform(self, instance_id: str, position: dict = None,
                                        rotation: dict = None, scale: dict = None) -> Optional[Dict[str, Any]]:
        self._check()
        data = {}
        if position is not None:
            data["position"] = position
        if rotation is not None:
            data["rotation"] = rotation
        if scale is not None:
            data["scale"] = scale
        if not data:
            return None
        result = self.client.table("scene_products").update(data).eq("instance_id", instance_id).execute()
        if not result.data:
            return None
        return self._scene_product_to_dict(result.data[0])

    def delete_scene_product(self, instance_id: str) -> bool:
        self._check()
        result = self.client.table("scene_products").delete().eq("instance_id", instance_id).execute()
        return len(result.data) > 0

    # ── Material Metadata CRUD ──────────────────────────────────────────

    def get_material(self, build_id: str) -> Optional[Dict[str, Any]]:
        self._check()
        result = self.client.table("material_metadata").select("*").eq("build_id", build_id).execute()
        if not result.data:
            return None
        return result.data[0].get("metadata", {})

    def save_material(self, build_id: str, metadata: dict) -> Dict[str, Any]:
        self._check()
        # Upsert by build_id
        data = {"build_id": build_id, "metadata": metadata}
        result = self.client.table("material_metadata").upsert(data, on_conflict="build_id").execute()
        return result.data[0].get("metadata", {})

    # ── Serialization helpers ───────────────────────────────────────────

    def _project_to_dict(self, row: dict) -> Dict[str, Any]:
        return {
            "id": str(row.get("id", "")),
            "name": row.get("name", "Untitled Project"),
            "description": row.get("description"),
            "user_id": row.get("user_id"),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
            "build_count": 0,
        }

    def _build_to_dict(self, row: dict) -> Dict[str, Any]:
        return {
            "id": str(row.get("id", "")),
            "project_id": str(row.get("project_id", "")),
            "build_id": row.get("build_id", ""),
            "prompt": row.get("prompt", ""),
            "code": row.get("code"),
            "parameters": row.get("parameters"),
            "explanation": row.get("explanation"),
            "stl_path": row.get("stl_path"),
            "step_path": row.get("step_path"),
            "script_path": row.get("script_path"),
            "is_modification": row.get("is_modification", False),
            "created_at": row.get("created_at"),
        }

    def _message_to_dict(self, row: dict) -> Dict[str, Any]:
        return {
            "id": str(row.get("id", "")),
            "project_id": str(row.get("project_id", "")),
            "role": row.get("role", ""),
            "content": row.get("content", ""),
            "build_result": row.get("build_result"),
            "status": row.get("status"),
            "created_at": row.get("created_at"),
        }

    def _version_to_dict(self, row: dict) -> Dict[str, Any]:
        return {
            "id": str(row.get("id", "")),
            "build_id": row.get("build_id", ""),
            "label": row.get("label", "Snapshot"),
            "code": row.get("code"),
            "parameters": row.get("parameters"),
            "explanation": row.get("explanation"),
            "prompt": row.get("prompt"),
            "created_at": row.get("created_at"),
        }

    def _scene_to_dict(self, row: dict) -> Dict[str, Any]:
        return {
            "sceneId": str(row.get("id", "")),
            "name": row.get("name", "Default Scene"),
            "projectId": row.get("project_id"),
            "products": [],
            "createdAt": row.get("created_at"),
        }

    def _scene_product_to_dict(self, row: dict) -> Dict[str, Any]:
        return {
            "instanceId": row.get("instance_id", ""),
            "buildId": row.get("build_id", ""),
            "instanceName": row.get("instance_name", ""),
            "stlUrl": row.get("stl_url", ""),
            "productType": row.get("product_type", ""),
            "position": row.get("position", {"x": 0, "y": 0, "z": 0}),
            "rotation": row.get("rotation", {"x": 0, "y": 0, "z": 0}),
            "scale": row.get("scale", {"x": 1, "y": 1, "z": 1}),
            "designData": row.get("design_data"),
        }

    # ── Analytics / feedback / share / GDPR ──────────────────────────

    def save_analytics(self, **fields) -> None:
        """Insert a row into build_analytics. Swallows errors (best-effort)."""
        try:
            self._check()
            allowed = {
                "build_id", "project_id", "user_id", "prompt", "model",
                "complexity", "duration_ms", "self_heal_attempts", "cache_hit",
                "success", "error_category", "error_message", "input_tokens",
                "output_tokens", "request_id",
            }
            row = {k: v for k, v in fields.items() if k in allowed and v is not None}
            if not row.get("build_id"):
                return
            self.client.table("build_analytics").insert(row).execute()
        except Exception as e:
            print(f"⚠️  save_analytics skipped: {e}")

    def save_feedback(self, build_id: str, user_id: Optional[str], rating: int, note: str = "") -> None:
        self._check()
        row = {"build_id": build_id, "rating": rating, "note": note[:2000]}
        if user_id:
            row["user_id"] = user_id
        # Upsert on (build_id, user_id) — users can toggle their rating
        self.client.table("build_feedback").upsert(row, on_conflict="build_id,user_id").execute()

    def create_share_link(self, token: str, build_id: str, owner_id: Optional[str]) -> dict:
        self._check()
        row = {"token": token, "build_id": build_id}
        if owner_id:
            row["owner_id"] = owner_id
        result = self.client.table("share_links").insert(row).execute()
        return (result.data or [{}])[0]

    def resolve_share_link(self, token: str) -> Optional[dict]:
        self._check()
        result = self.client.table("share_links").select("*").eq("token", token).limit(1).execute()
        rows = result.data or []
        if not rows:
            return None
        link = rows[0]
        expires_at = link.get("expires_at")
        if expires_at:
            from datetime import datetime, timezone
            try:
                if datetime.fromisoformat(expires_at.replace("Z", "+00:00")) < datetime.now(timezone.utc):
                    return None
            except Exception:
                pass
        # Fetch the build row
        build_id = link.get("build_id")
        builds = self.client.table("builds").select("*").eq("build_id", build_id).limit(1).execute()
        build_row = (builds.data or [None])[0]
        # Bump view counter (best effort)
        try:
            self.client.table("share_links").update(
                {"view_count": (link.get("view_count") or 0) + 1}
            ).eq("token", token).execute()
        except Exception:
            pass
        return {
            "buildId": build_id,
            "build": self._build_to_dict(build_row) if build_row else None,
            "viewCount": (link.get("view_count") or 0) + 1,
        }

    def export_user_data(self, user_id: str) -> dict:
        """Dump all user-owned rows for GDPR compliance."""
        self._check()
        projects = self.client.table("projects").select("*").eq("user_id", user_id).execute().data or []
        project_ids = [p["id"] for p in projects]
        builds = []
        messages = []
        if project_ids:
            builds = self.client.table("builds").select("*").in_("project_id", project_ids).execute().data or []
            messages = self.client.table("chat_messages").select("*").in_("project_id", project_ids).execute().data or []
        analytics = self.client.table("build_analytics").select("*").eq("user_id", user_id).execute().data or []
        feedback = self.client.table("build_feedback").select("*").eq("user_id", user_id).execute().data or []
        shares = self.client.table("share_links").select("*").eq("owner_id", user_id).execute().data or []
        return {
            "projects": projects,
            "builds": builds,
            "messages": messages,
            "analytics": analytics,
            "feedback": feedback,
            "shareLinks": shares,
        }

    def delete_user_data(self, user_id: str) -> dict:
        """Delete all user-owned rows. Cascades handle builds/messages."""
        self._check()
        # Anonymize analytics + feedback instead of deleting (keeps aggregate stats clean)
        self.client.table("build_analytics").update({"user_id": None}).eq("user_id", user_id).execute()
        self.client.table("build_feedback").update({"user_id": None}).eq("user_id", user_id).execute()
        self.client.table("share_links").delete().eq("owner_id", user_id).execute()
        # Delete projects (cascades to builds, chat_messages, version_history)
        result = self.client.table("projects").delete().eq("user_id", user_id).execute()
        return {"projectsDeleted": len(result.data or [])}

    def summarize_user_tokens(self, user_id: str) -> dict:
        """Aggregate the user's token usage for today and this month.

        Reads from build_analytics. Cost is estimated client-side via the
        token_tracker pricing table to keep the DB free of pricing concerns.
        """
        self._check()
        import datetime as _dt
        from services.token_tracker import estimate_cost

        now = _dt.datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

        def _sum(since_iso: str) -> dict:
            try:
                res = (
                    self.client.table("build_analytics")
                    .select("model,input_tokens,output_tokens")
                    .eq("user_id", user_id)
                    .gte("created_at", since_iso)
                    .execute()
                )
                rows = res.data or []
            except Exception:
                rows = []
            inp = out = 0
            cost = 0.0
            for r in rows:
                i = int(r.get("input_tokens") or 0)
                o = int(r.get("output_tokens") or 0)
                inp += i
                out += o
                c = estimate_cost(r.get("model") or "", i, o)
                if c is not None:
                    cost += c
            return {
                "input_tokens": inp,
                "output_tokens": out,
                "builds": len(rows),
                "cost_usd": round(cost, 4),
            }

        return {
            "today": _sum(today_start),
            "month": _sum(month_start),
        }


# ── Module-level singleton ──────────────────────────────────────────────
database_service = DatabaseService()
