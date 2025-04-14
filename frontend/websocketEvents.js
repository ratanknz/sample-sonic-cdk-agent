tools: [
    {
      toolSpec: {
        name: "lookup",
        description:
          "Runs query against a knowledge base to retrieve information.",
        inputSchema: {
          json: JSON.stringify({
            $schema: "http://json-schema.org/draft-07/schema#",
            type: "object",
            properties: {
              query: {
                type: "string",
                description: "the query to search",
              },
            },
            required: ["query"],
          }),
        },
      },
    },
    {
      toolSpec: {
        name: "userProfileSearch",
        description:
          "Search for a user's account and phone plan information by phone number",
        inputSchema: {
          json: JSON.stringify({
            $schema: "http://json-schema.org/draft-07/schema#",
            type: "object",
            properties: {
              airpoints_number: {
                type: "string",
                description: "the user's phone number",
              },
            },
            required: ["airpoints_number"],
          }),
        },
      },
    },
  ];