## Check for following in the log 
1. Search by "Tool use detected" string to confirm if LLM recommended right tool with correct query parameters 
2. "Tool Result Event" to make sure that output of tool call is correct. Make sure you disable it as it might produce large amount of log.
3. if bot is not responding at all, force redployment of the ECS Service by going to Cluster --> Service (select service and then click update button)