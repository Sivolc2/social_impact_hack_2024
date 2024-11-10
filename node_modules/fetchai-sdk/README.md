# FetchAI SDK

FetchAI SDK is a JavaScript/TypeScript library for interacting with the AgentVerse API. It allows you to create, manage, and interact with AI agents.

## Installation

To install the FetchAI SDK, use npm:

```sh
npm install fetchai-sdk
```

## Usage

### Importing the SDK

```typescript
import FetchAI from "fetchai-sdk";
```

### Authenticating with an API Token

To use the FetchAI SDK, you need to authenticate with an API token. You can obtain this token from the AgentVerse platform.

```typescript
const { fetchAI } = new FetchAI("your-api-token");
```

### Creating an Agent

Here is an example of how to create a new agent:

```typescript
async function createAgent() {
  try {
    const agent = await fetchAI.createAgent("MyNewAgent");
    console.log("Agent created:", agent);
  } catch (error) {
    console.error("Error creating agent:", error);
  }
}
createAgent();
```

### Sample Response

The response from creating an agent will look like this:

```json
{
  "name": "MyNewAgent",
  "address": "agent-address",
  "running": false,
  "compiled": true,
  "revision": 1,
  "code_digest": "digest-string",
  "wallet_address": "wallet-address"
}
```

## API Reference

For detailed API reference, please refer to the [documentation](https://agentverse.ai/docs).

## License

This project is licensed under the ISC License - see the [LICENSE](LICENSE) file for details.
