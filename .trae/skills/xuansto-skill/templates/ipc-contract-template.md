# IPC Channel Contract Template

## Channel: `channel:name`

| Field | Value |
|-------|-------|
| Direction | main→renderer / renderer→main |
| Description | Brief description of what this channel does |
| Since Version | 1.0.0 |
| Status | draft / stable / deprecated |

---

## Request Parameters

| Parameter | Type | Required | Description | Constraints |
|-----------|------|----------|-------------|-------------|
| `action` | string | Yes | The action to perform | Must be one of: `create`, `read`, `update`, `delete` |
| `payload.id` | string(uuid) | Yes | Resource identifier | Valid UUID v4 format |
| `payload.data` | object | No | Additional data for the request | Max size: 1MB |

### Request Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "action": {
      "type": "string",
      "enum": ["create", "read", "update", "delete"],
      "description": "The action to perform"
    },
    "payload": {
      "type": "object",
      "properties": {
        "id": { "type": "string", "format": "uuid" },
        "data": { "type": "object" }
      },
      "required": ["id"]
    }
  },
  "required": ["action", "payload"],
  "additionalProperties": false
}
```

---

## Response Data

### Success Response

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `success` | boolean | Yes | Always `true` for success |
| `data` | object | Yes | Response payload |
| `timestamp` | string(date-time) | No | ISO 8601 timestamp |

### Error Response

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `success` | boolean | Yes | Always `false` for error |
| `error.code` | string | Yes | Machine-readable error code |
| `error.message` | string | Yes | Human-readable error description |
| `error.details` | object | No | Additional error context |

### Response Schema

```json
{
  "success": {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
      "success": { "type": "boolean", "const": true },
      "data": { "type": "object" },
      "timestamp": { "type": "string", "format": "date-time" }
    },
    "required": ["success", "data"]
  },
  "error": {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
      "success": { "type": "boolean", "const": false },
      "error": {
        "type": "object",
        "properties": {
          "code": { "type": "string" },
          "message": { "type": "string" },
          "details": { "type": "object" }
        },
        "required": ["code", "message"]
      }
    },
    "required": ["success", "error"]
  }
}
```

---

## Error Handling

| Error Code | Description | Recovery Strategy |
|------------|-------------|-------------------|
| `ERR_INVALID_PARAMS` | Request parameters validation failed | Check request schema and retry |
| `ERR_PERMISSION_DENIED` | Caller lacks required permission | Request permission from user |
| `ERR_TIMEOUT` | Operation timed out | Retry with exponential backoff |
| `ERR_NOT_FOUND` | Requested resource not found | Verify resource ID and retry |
| `ERR_INTERNAL` | Unexpected internal error | Log error and report to user |

---

## Security Constraints

- **Input Validation**: All request parameters MUST be validated against the request schema before processing
- **Rate Limiting**: Maximum 100 requests per second per channel per renderer process
- **Permission Scope**: Channel requires `fs:read` permission scope
- **Data Sanitization**: All string inputs MUST be sanitized to prevent injection attacks
- **Origin Validation**: Only whitelisted renderer origins may invoke this channel
- **Payload Size**: Maximum payload size is 10MB

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | YYYY-MM-DD | Initial contract definition | — |
| | | | |

---

## Implementation Examples

### Electron (ipcMain / ipcRenderer)

#### Main Process (Handler)

```javascript
const { ipcMain } = require('electron');

ipcMain.handle('channel:name', async (event, request) => {
  try {
    const validated = validateRequest(request);
    if (!validated.success) {
      return {
        success: false,
        error: {
          code: 'ERR_INVALID_PARAMS',
          message: 'Request validation failed',
          details: validated.errors
        }
      };
    }

    const result = await performAction(request);
    return {
      success: true,
      data: result,
      timestamp: new Date().toISOString()
    };
  } catch (err) {
    return {
      success: false,
      error: {
        code: err.code || 'ERR_INTERNAL',
        message: err.message,
        details: {}
      }
    };
  }
});
```

#### Preload Script (Bridge)

```javascript
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  channelName: (payload) => ipcRenderer.invoke('channel:name', payload)
});
```

#### Renderer Process (Caller)

```javascript
const response = await window.api.channelName({
  action: 'read',
  payload: { id: '123e4567-e89b-12d3-a456-426614174000' }
});

if (response.success) {
  console.log('Data:', response.data);
} else {
  console.error('Error:', response.error);
}
```

### Tauri (invoke / listen)

#### Rust Command (Handler)

```rust
use tauri::command;
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize)]
pub struct ChannelNameRequest {
    action: String,
    payload: ChannelNamePayload,
}

#[derive(Debug, Deserialize)]
pub struct ChannelNamePayload {
    id: String,
    data: Option<serde_json::Value>,
}

#[derive(Debug, Serialize)]
pub struct ChannelNameResponse {
    success: bool,
    data: Option<serde_json::Value>,
    error: Option<ChannelNameError>,
    timestamp: String,
}

#[derive(Debug, Serialize)]
pub struct ChannelNameError {
    code: String,
    message: String,
    details: Option<serde_json::Value>,
}

#[command]
pub async fn channel_name(request: ChannelNameRequest) -> ChannelNameResponse {
    match perform_action(request).await {
        Ok(data) => ChannelNameResponse {
            success: true,
            data: Some(data),
            error: None,
            timestamp: chrono::Utc::now().to_rfc3339(),
        },
        Err(err) => ChannelNameResponse {
            success: false,
            data: None,
            error: Some(ChannelNameError {
                code: err.code.to_string(),
                message: err.message,
                details: None,
            }),
            timestamp: chrono::Utc::now().to_rfc3339(),
        },
    }
}
```

#### Frontend (Caller)

```typescript
import { invoke } from '@tauri-apps/api/core';

const response = await invoke<ChannelNameResponse>('channel_name', {
  request: {
    action: 'read',
    payload: { id: '123e4567-e89b-12d3-a456-426614174000' },
  },
});

if (response.success) {
  console.log('Data:', response.data);
} else {
  console.error('Error:', response.error);
}
```

#### Tauri Event (main→renderer push)

```rust
use tauri::Manager;

app_handle.emit("channel:name:event", &payload)?;
```

```typescript
import { listen } from '@tauri-apps/api/event';

const unlisten = await listen<ChannelNamePayload>('channel:name:event', (event) => {
  console.log('Received:', event.payload);
});

unlisten();
```

---

## Contract Checklist

- [ ] Channel name follows naming convention (`namespace:action`)
- [ ] Request schema defined with `additionalProperties: false`
- [ ] Response schema covers both success and error cases
- [ ] All error codes documented with recovery strategies
- [ ] Security constraints specified
- [ ] Rate limiting configured
- [ ] Input validation implemented
- [ ] Preload bridge exposes only necessary channels
- [ ] Integration tests cover all error paths
- [ ] Contract version recorded
