# Objects

## Message Content

```json
{
    "type": "object",
    "properties": {
        "text": {
            "type": "string",
            "maxLength": 8192
        },
        "json": {
            "type": "object",
            "additionalProperties": true
        },
        "files": {
            "type": "array",
            "items": {
                "type": "string",
                "contentEncoding": "base64",
                "contentMediaType": {
                    "type": "string",
                    "enum": [
                        "text/plain",
                        "text/markdown",
                        "application/pdf",
                        "image/jpeg",
                        "image/png"
                    ]
                }
            }
        }
    }
}
```

## Message

Represents a message in the conversation thread.

- **Id**: The unique identifier for the message within the thread.
- **Role**: The role of the message originator. Either "user" or "assistant".
- **Content**: The content of the message.
- **Timestamp**: The timestamp when the message was created.

```json
{
    "type": "object",
    "properties": {
        "id": {
            "type": "string"
        },
        "role": {
            "type": "string",
            "enum": [
                "user",
                "assistant"
            ]
        },
        "content": {
            "type": "messageContent"
        },
        "timestamp": {
            "type": "string",
            "format": "date-time"
        }
    }
}
```

## Thread

```json
{
    "type": "object",
    "properties": {
        "id": {
            "type": "string"
        },
        "title": {
            "type": "string"
        },
        "messages": {
            "type": "array",
            "items": {
                "$ref": "../objects/message.json"
            }
        }
    }
}
```

## Thread Info

- **Id**: The unique identifier for the thread.
- **Title**: The title of the thread.
- **Created At**: The timestamp when the thread was created.
- **Updated At**: The timestamp when the thread was last updated.
- **Token Count**: The number of tokens in the thread.
- **Message Count**: The number of messages in the thread.

```json
{
    "type": "object",
    "properties": {
        "id": {
            "type": "string"
        },
        "title": {
            "type": "string"
        },
        "createdAt": {
            "type": "string",
            "format": "date-time"
        },
        "updatedAt": {
            "type": "string",
            "format": "date-time"
        },
        "tokenCount": {
            "type": "integer"
        },
        "messageCount": {
            "type": "integer"
        }
    }
}
```