nexus_guidelines = """NEXUS FRAMEWORK - A HIGH-LEVEL GUIDE
1. OVERVIEW
Nexus is an advanced framework for building hierarchical AI agent systems that enables coordinated task execution through specialized agents and supervisors.

2. CORE ARCHITECTURE
   A. Supervisor Layer
      • Controls overall workflow coordination
      • Manages agent delegation and communication
      • Can be hierarchically structured
   
   B. Agent Layer  
      • Performs specialized tasks
      • Contains domain-specific knowledge
      • Can be stateful or stateless
      • Can enforce structured outputs using schemas
   
   C. Tool Layer
      • Extends agent capabilities
      • Provides specific functionalities
      • Integrates with external systems

3. KEY COMPONENTS
   A. Main Supervisor
      • Top-level coordinator
      • Manages workflow distribution
      • Handles high-level decision making
   
   B. Assistant Supervisors
      • Domain-specific coordinators
      • Manage subset of agents
      • Handle specialized workflows
   
   C. Specialized Agents
      • Task-focused AI entities
      • Configurable behavior
      • Tool integration capability
      • Can enforce structured outputs

4. OUTPUT SCHEMAS
   A. Purpose
      • Ensure consistent agent responses
      • Validate output structure
      • Enable reliable downstream processing
   
   B. Schema Configuration
      • Define expected response format
      • Specify required fields
      • Set validation constraints
   
   C. Validation Modes
      • Strict: Always enforce schema
      • Non-strict: Allow fallback to unstructured
   
   D. Common Schema Types
      • Analysis results
      • Code generation
      • Data processing
      • Content creation

5. SCHEMA EXAMPLES
   Analysis Schema:
   {
     "type": "object",
     "properties": {
       "summary": {"type": "string", "description": "Brief analysis summary"},
       "key_points": {
         "type": "array",
         "items": {"type": "string"},
         "description": "List of key findings"
       },
       "recommendations": {
         "type": "array",
         "items": {"type": "string"},
         "description": "Suggested actions"
       }
     },
     "required": ["summary", "key_points"]
   }

   Code Schema:
   {
     "type": "object",
     "properties": {
       "description": {"type": "string", "description": "Code explanation"},
       "code": {"type": "string", "description": "Implementation"},
       "language": {"type": "string", "description": "Programming language"}
     },
     "required": ["description", "code"]
   }

   Content Schema:
   {
     "type": "object",
     "properties": {
       "title": {"type": "string", "description": "Content title"},
       "body": {"type": "string", "description": "Main content"},
       "metadata": {
         "type": "object",
         "properties": {
           "category": {"type": "string"},
           "tags": {"type": "array", "items": {"type": "string"}}
         }
       }
     },
     "required": ["title", "body"]
   }
"""

expanded_workflow = """Below is a detailed, yet simplified, workflow design for bedtime story generation using the Nexus framework guidelines. Each component’s role, responsibilities, and interactions are described following the Nexus’s Supervisor, Agent, and Tool layers.

──────────────────────────────
1. Main Supervisor

Role:
• Acts as the top-level coordinator for the entire bedtime story generation workflow.

Responsibilities:
• Receives the initial request for a bedtime story.
• Determines overall story parameters (such as tone, length, and target audience) from any user inputs or defaults.
• Delegates the generation tasks to specialized assistant components.
• Oversees the communication flow and collects the final output from the agents before passing it back to the user.

──────────────────────────────
2. Assistant Supervisor – Story Structure Coordinator

Role:
• Functions as a domain-specific coordinator focused on narrative aspects.

Responsibilities:
• Breaks down the story generation task into clear narrative components (introduction, conflict, resolution).
• Determines style guidelines (such as soothing tone, simple language, and engaging storytelling) suitable for a bedtime context.
• Coordinating with the Specialized Agent to ensure that the generated narrative adheres to the desired structure and style.

──────────────────────────────
3. Specialized Agent – Story Content Generator

Role:
• A task-focused AI entity responsible for generating creative story content.

Responsibilities:
• Uses domain-specific knowledge to generate a bedtime story based on the parameters and narrative structure set by the assistant supervisor.
• Ensures that the story is engaging, calming, and age-appropriate.
• Can be configured to produce story variations should the user require alternative options.
• Handles iterative improvements if minor adjustments are needed (for example, softening certain parts of the narrative).

──────────────────────────────
4. Tool Layer Component – Language Generation/Enhancement Tool

Role:
• Extends the agent’s capability by providing specialized text generation and language processing functions.

Responsibilities:
• Integrates with the underlying language model to convert narrative outlines into a full prose story.
• Refines the language, ensuring that it flows naturally and is optimized for a bedtime storytelling experience.
• May include post-generation editing functions such as grammar checks and style adjustments.
• Operates as a plug-in resource that the Story Content Generator calls to ensure that the final text is both creative and polished.

──────────────────────────────
Workflow Summary

1. The Main Supervisor receives a request for a bedtime story and determines overall parameters.
2. The Main Supervisor delegates narrative planning to the Assistant Supervisor, which organizes story structure and style guidelines.
3. The Specialized Agent (Story Content Generator) creates the narrative, leveraging the language processing capabilities of the Tool Layer.
4. The Tool Layer refines the text, ensuring smooth language and intended tone.
5. Finally, the Main Supervisor collects the refined bedtime story and returns it to the user in a straightforward, easy-to-understand manner.

──────────────────────────────
This streamlined workflow leverages the hierarchical and coordinated nature of the Nexus framework while ensuring that the components are clear in their roles and interactions. The design keeps the process simple, yet modular enough to allow future adjustments such as additional personalization or more complex narrative elements, if needed."""

