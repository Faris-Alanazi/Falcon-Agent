# Falcon Agent - Agent Specifications

This document provides detailed information about each specialized agent in the Falcon Agent system.

## 1. Requirementer Agent

**Primary Function**: Serves as the entry point to the system, analyzing user requests deeply and refining them into a comprehensive Product Requirement Document (PRD).

**Key Capabilities**:
- Deep analysis of user requests through reasoning and iterative refinement
- Strategic questioning to clarify user requirements with minimal interruption
- Internet search capabilities to enhance and validate requirements
- Autonomous decision-making on when additional information is needed

**Memory Architecture**:
- **Long-term memory**: Stores domain knowledge, patterns from previous projects, and user preferences
- **Short-term memory**: Maintains context of current conversation and requirement details

**Tools**:
- **Search_Internet**: Utilizes Brave search to access up-to-date information
- **Sequential_Thinking**: Employs methodical analysis of requirements

**Operational Flow**:
1. Receives initial user request
2. Performs deep analysis to understand core requirements
3. Asks clarifying questions only when necessary
4. Searches internet for relevant information when needed
5. Iteratively refines understanding until complete
6. Produces formal PRD document for the Tasker agent

## 2. Tasker Agent

**Primary Function**: Transforms the PRD into an actionable "Goal Graph" - a hierarchical representation of tasks required to fulfill the requirements.

**Key Capabilities**:
- Creation of comprehensive task dependency graphs
- Deep analysis of requirements to identify all necessary implementation steps
- Self-validation through iterative refinement of the Goal Graph
- Dependency mapping to ensure logical task sequencing

**Memory Architecture**:
- **Long-term memory**: Stores knowledge about software development patterns, common task structures, and technical dependencies
- **Short-term memory**: Maintains current PRD context and evolving Goal Graph structure

**Tools**:
- **Search_Internet**: Accesses information for technical requirements
- **Sequential_Thinking**: Enables methodical analysis of requirements
- **Graph CRUD tools**: For creating, reading, updating, and deleting nodes in the Goal Graph

**Task Node Structure**:
- **Task ID**: Unique identifier for the task
- **Name**: Descriptive task name
- **Priority**: Task importance level (High, Medium, Low)
- **Detailed Description**: Comprehensive explanation of what the task entails
- **Dependencies**: List of tasks that must be completed before this task
- **Task Status**: Current state (Not Started, In-Progress, Needs Review, etc.)
- **Task Messages**: Communication history between agents
- **Owner**: Agent responsible for execution
- **Approval Status**: Indication of quality approval

## 3. Goaler Agent

**Primary Function**: Serves as a supervisor, validating that the Goal Graph accurately represents a complete path to fulfilling the original user requirements.

**Key Capabilities**:
- Comprehensive analysis of Goal Graph completeness and accuracy
- Cross-validation between original user requirements, PRD, and Goal Graph
- Feedback provision to Tasker agent for refinement
- Final approval of Goal Graph before execution

**Memory Architecture**:
- **Long-term memory**: Stores knowledge about software architecture, project management, and quality assurance
- **Short-term memory**: Maintains context of current PRD and Goal Graph under review

**Tools**:
- **Search_Internet**: Access to validation information
- **Sequential_Thinking**: For methodical validation of the Goal Graph

**Operational Flow**:
1. Receives Goal Graph from Tasker agent
2. Reviews original user requirements and PRD
3. Analyzes Goal Graph for completeness, accuracy, and alignment with requirements
4. Provides feedback to Tasker agent if issues are found
5. Approves Goal Graph when satisfied with its quality
6. Initiates Coder agents when Goal Graph is approved

## 4. Coder Agents

**Primary Function**: Form a collaborative team that implements the code according to the Goal Graph specifications.

**Key Capabilities**:
- Collaborative work on shared file system
- Task selection and management based on dependencies
- Code implementation according to task specifications
- Status updates and review requests
- Conflict resolution in shared resources

**Memory Architecture**:
- **Long-term memory**: Stores programming knowledge, design patterns, and best practices
- **Short-term memory**: Maintains context of current tasks and code being developed

**Tools**:
- **Search_Internet**: Access to technical information
- **File system tools**: For file management with locking mechanisms
- **Sequential_Thinking**: For methodical code development
- **Context7**: Access to latest documentation for programming languages and frameworks

**Operational Rules**:
- Maximum of 2 tasks simultaneously per agent
- File locking before editing to prevent conflicts
- Task status updates as progress is made
- Review requests when tasks are complete
- Visibility into other team members' work
- Response to feedback from Qualitator agent

## 5. Qualitator Agent

**Primary Function**: Ensures code quality and alignment with requirements through comprehensive review.

**Key Capabilities**:
- Code review against task specifications and best practices
- Feedback provision to Coder agents for improvements
- Final approval of completed tasks
- Quality assurance across the entire codebase

**Memory Architecture**:
- **Long-term memory**: Stores knowledge about code quality standards, common issues, and best practices
- **Short-term memory**: Maintains context of current tasks under review

**Tools**:
- **Search_Internet**: Access to validation information
- **File system tools**: Read-only access to files (even while locked by Coders)
- **Context7**: Access to latest documentation to validate implementation correctness

**Operational Flow**:
1. Monitors for tasks with "Needs Review" status
2. Reviews code against task specifications and best practices
3. Provides detailed feedback to Coder agents if issues are found
4. Approves tasks when satisfied with implementation quality
5. Updates task status to "Completed" when approved
6. Notifies Communicator agent when all tasks are complete

## 6. Communicator Agent

**Primary Function**: Provides the final communication to the user, presenting the completed project and relevant information.

**Key Capabilities**:
- Comprehensive project visibility across all stages
- Clear communication of outcomes and results
- Summary generation of development process
- Presentation of final deliverables

**Memory Architecture**:
- **Long-term memory**: Stores communication patterns and project history
- **Short-term memory**: Maintains context of current project status and outcomes

**Operational Flow**:
1. Monitors overall project progress
2. Collects information about completed tasks and outcomes
3. Generates comprehensive summary of development process
4. Presents final deliverables to user in clear, accessible format
5. Provides any necessary instructions or documentation 