# Altron API Endpoints

## General

## Sub Processes

### Create Job

```json
"endpoint": "subprocess/job/create"

"method": "POST"

"description": "Create a new process job."

"parameters": [
    {
        "name": "job",
        "description": "The process job to create.",
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "The title of the process job."
            },
            "description": {
                "type": "string",
                "description": "The description of the process job."
            },
            "priority": {
                "type": "integer",
                "description": "The priority of the process job."
            }
        },
        "required": true
    }
]

"response": {
    200: {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "The ID of the created process job."
            },
            "title": {
                "type": "string",
                "description": "The title of the process job."
            },
            "description": {
                "type": "string",
                "description": "The description of the process job."
            },
            "priority": {
                "type": "integer",
                "description": "The priority of the process job."
            },
            "created_at": {
                "type": "string",
                "description": "The creation date of the process job."
            }
        }
    },
    400: {
        "type": "object",
        "properties": {
            "error": {
                "type": "string",
                "description": "The error message."
            }
        }
    },
    500: {
        "type": "object",
        "properties": {
            "error": {
                "type": "string",
                "description": "The error message."
            }
        }
    }
}
```

### Get Status

```json
"endpoint": "subprocess/job/get_status"

"method": "GET"

"description": "Get the status of a process job."
```

### Get Result

```json
"endpoint": "subprocess/job/get_result"

"method": "GET"

"description": "Get the result of a process job."
```

### Terminate

```json
"endpoint": "subprocess/job/terminate"

"method": "DELETE"

"description": "Terminate a process job."
```

## Discord

### Message

```json
"endpoint": "/discord/message"

"method": "POST"

"description": "Send a list of Discord messages to Altron."

"parameters": [
    {
        "name": "messages",
        "description": "A list of Discord messages to send to Altron.",
        "type": "array",
        "elements": {
            "messaage": {
                "type": "object",
                "properties": {
                    "sender": {
                        "type": "string",
                        "description": "The sender of the message."
                    },
                    "text": {
                        "type": "string",
                        "description": "The text of the message."
                    },
                    "image": {
                        "type": "string" | "bytes" | null,
                        "description": "The image of the message."
                    }
                }
            }
        },
        "required": true
    }
]

"response": {
    200: {
        "type": "object",
        "properties": {
            "sender": {
                "type": "string",
                "description": "The sender of the message."
            },
            "text": {
                "type": "string",
                "description": "The text of the message."
            },
            "image": {
                "type": "string" | "bytes" | null,
                "description": "The image of the message."
            }
        }
    },
    400: {
        "type": "object",
        "properties": {
            "error": {
                "type": "string",
                "description": "An external error message."
            }
        }
    },
    500: {
        "type": "object",
        "properties": {
            "error": {
                "type": "string",
                "description": "An internal error message."
            }
        }
    }
}
```


