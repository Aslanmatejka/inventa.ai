import React, { useState, useRef, useCallback, useEffect } from 'react';
import { createCollabRoom, getCollabRoom, connectToCollabRoom } from '../api';
import './CollabPanel.css';

/**
 * F35: Real-time Collaboration Panel
 * Create/join rooms, see members, chat, sync scene state.
 */
function CollabPanel({ sceneId, onSceneSync }) {
  const [expanded, setExpanded] = useState(false);
  const [roomId, setRoomId] = useState('');
  const [joinInput, setJoinInput] = useState('');
  const [connected, setConnected] = useState(false);
  const [members, setMembers] = useState([]);
  const [myName, setMyName] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [creating, setCreating] = useState(false);
  const wsRef = useRef(null);

  const cleanup = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnected(false);
    setMembers([]);
    setChatMessages([]);
    setRoomId('');
    setMyName('');
  }, []);

  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const handleMessage = useCallback((data) => {
    switch (data.type) {
      case 'room_joined':
        setConnected(true);
        setMyName(data.memberName || '');
        setMembers(data.members || []);
        break;

      case 'member_joined':
        setMembers(prev => [...prev, { name: data.name, isHost: false }]);
        setChatMessages(prev => [...prev, { system: true, text: `${data.name} joined` }]);
        break;

      case 'member_left':
        setMembers(prev => prev.filter(m => m.name !== data.name));
        setChatMessages(prev => [...prev, { system: true, text: `${data.name} left` }]);
        break;

      case 'chat_message':
        setChatMessages(prev => [...prev, { from: data.from, text: data.text, time: data.timestamp }]);
        break;

      case 'scene_sync':
        if (onSceneSync) {
          onSceneSync(data.sceneState, data.updatedBy);
        }
        setChatMessages(prev => [...prev, { system: true, text: `${data.updatedBy} updated the scene` }]);
        break;

      case 'name_changed':
        setMembers(prev => prev.map(m => m.name === data.oldName ? { ...m, name: data.newName } : m));
        break;

      case 'error':
        alert('Collab error: ' + data.message);
        cleanup();
        break;

      default:
        break;
    }
  }, [onSceneSync, cleanup]);

  const handleCreate = async () => {
    setCreating(true);
    try {
      const name = `User_${Math.floor(Math.random() * 9000) + 1000}`;
      const res = await createCollabRoom(name, sceneId || '');
      if (res.success) {
        setRoomId(res.roomId);
        // Connect via WebSocket
        const ws = connectToCollabRoom(res.roomId, handleMessage);
        ws.onopen = () => setConnected(true);
        ws.onclose = () => {
          setConnected(false);
          setChatMessages(prev => [...prev, { system: true, text: 'Disconnected from room' }]);
        };
        wsRef.current = ws;
      }
    } catch (err) {
      console.error('Failed to create room:', err);
    } finally {
      setCreating(false);
    }
  };

  const handleJoin = async () => {
    const id = joinInput.trim();
    if (!id) return;
    try {
      // Verify room exists
      await getCollabRoom(id);
      setRoomId(id);
      const ws = connectToCollabRoom(id, handleMessage);
      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        setChatMessages(prev => [...prev, { system: true, text: 'Disconnected from room' }]);
      };
      wsRef.current = ws;
    } catch (err) {
      alert('Room not found: ' + id);
    }
  };

  const handleSendChat = () => {
    if (!chatInput.trim() || !wsRef.current) return;
    wsRef.current.send(JSON.stringify({ type: 'chat_message', text: chatInput.trim() }));
    setChatMessages(prev => [...prev, { from: myName, text: chatInput.trim(), mine: true }]);
    setChatInput('');
  };

  const handleLeave = () => {
    cleanup();
  };

  const copyRoomId = () => {
    navigator.clipboard.writeText(roomId);
  };

  return (
    <div className="collab-panel">
      <button
        className="collab-panel__toggle"
        onClick={() => setExpanded(!expanded)}
      >
        <span>{connected ? '🟢' : '👥'} Collaborate</span>
        {connected && <span className="collab-panel__badge">{members.length}</span>}
        <span className={`collab-panel__arrow ${expanded ? 'open' : ''}`}>▸</span>
      </button>

      {expanded && (
        <div className="collab-panel__body">
          {!connected ? (
            <div className="collab-panel__connect">
              <button
                className="collab-panel__create-btn"
                onClick={handleCreate}
                disabled={creating}
              >
                {creating ? '⏳ Creating...' : '➕ Create Room'}
              </button>

              <div className="collab-panel__divider">or join existing</div>

              <div className="collab-panel__join-row">
                <input
                  type="text"
                  placeholder="Room ID"
                  value={joinInput}
                  onChange={(e) => setJoinInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleJoin()}
                  className="collab-panel__join-input"
                />
                <button className="collab-panel__join-btn" onClick={handleJoin}>
                  Join
                </button>
              </div>
            </div>
          ) : (
            <div className="collab-panel__room">
              {/* Room header */}
              <div className="collab-panel__room-header">
                <span className="collab-room-id" onClick={copyRoomId} title="Click to copy">
                  🔗 {roomId}
                </span>
                <button className="collab-panel__leave-btn" onClick={handleLeave}>Leave</button>
              </div>

              {/* Members */}
              <div className="collab-panel__members">
                {members.map((m, i) => (
                  <span key={i} className={`collab-member ${m.name === myName ? 'collab-member--me' : ''}`}>
                    {m.isHost && '👑 '}{m.name}{m.name === myName ? ' (you)' : ''}
                  </span>
                ))}
              </div>

              {/* Chat */}
              <div className="collab-panel__chat">
                <div className="collab-chat-messages">
                  {chatMessages.map((msg, i) => (
                    <div key={i} className={`collab-chat-msg ${msg.system ? 'system' : ''} ${msg.mine ? 'mine' : ''}`}>
                      {msg.system ? (
                        <span className="collab-chat-system">{msg.text}</span>
                      ) : (
                        <>
                          {!msg.mine && <span className="collab-chat-name">{msg.from}</span>}
                          <span className="collab-chat-text">{msg.text}</span>
                        </>
                      )}
                    </div>
                  ))}
                </div>
                <div className="collab-chat-input-row">
                  <input
                    type="text"
                    placeholder="Message..."
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSendChat()}
                    className="collab-chat-input"
                  />
                  <button className="collab-chat-send" onClick={handleSendChat}>↑</button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default CollabPanel;
