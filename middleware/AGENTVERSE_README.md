# Meeting Analysis Agent

## Description
An AI-powered agent that analyzes meeting transcripts and extracts:
- **Action items** with assignees, priorities, and due dates
- **Decisions** made during the meeting with rationale
- **Unresolved questions** that need follow-up
- **Participant summaries** showing contributions
- **Overall sentiment** analysis of the meeting

Powered by **Google Gemini 2.5 Flash** for fast, accurate, and cost-effective analysis.

## Input Format
Send a JSON object with the following structure:

```json
{
  "meeting_title": "Sprint Planning Q4",
  "meeting_date": "2024-10-25T14:00:00Z",
  "participants": ["Alice", "Bob", "Carol"],
  "transcript": [
    {
      "speaker": "Alice",
      "text": "Let's discuss the Q4 roadmap. We need to prioritize the API redesign.",
      "timestamp": "14:00:00"
    },
    {
      "speaker": "Bob",
      "text": "I'll handle the backend API by Friday. It's critical for the release.",
      "timestamp": "14:05:30"
    },
    {
      "speaker": "Carol",
      "text": "Should we also update the documentation?",
      "timestamp": "14:10:15"
    }
  ]
}
```

### Required Fields:
- `meeting_title` (string): Title or subject of the meeting
- `meeting_date` (string): ISO 8601 format date (e.g., "2024-10-25T14:00:00Z")
- `participants` (array): List of participant names
- `transcript` (array): List of transcript entries with:
  - `speaker` (string): Name of the person speaking
  - `text` (string): What was said
  - `timestamp` (string, optional): When it was said

### Optional Fields:
- `metadata` (object): Any additional metadata about the meeting

## Output Format
Returns a formatted analysis including:

### 1. Meeting Summary
Concise overview of what was discussed and decided

### 2. Action Items
Each action item includes:
- Task description
- Assigned person
- Priority level (critical, high, medium, low)
- Due date (if mentioned)
- Context from the conversation

### 3. Decisions
Key decisions made with:
- What was decided
- Rationale behind the decision
- Participants involved

### 4. Unresolved Questions
Questions that need follow-up with:
- The question text
- Who asked it
- Context

### 5. Sentiment Analysis
Overall tone of the meeting (positive, neutral, negative, mixed)

## Example Output

```
📊 **Meeting Analysis: Sprint Planning Q4**

📅 Date: 2024-10-25T14:00:00Z
🏷️  Type: Sprint Planning

**Summary:**
The team discussed Q4 priorities focusing on API redesign. Bob committed to completing the backend API by Friday, which is critical for the upcoming release. Documentation updates were raised as a potential concern.

**✅ Action Items (1):**
1. **Complete backend API redesign**
   - Assignee: Bob
   - Priority: high
   - Due: Friday

**🎯 Decisions (1):**
1. Prioritize API redesign for Q4 release
   - Rationale: Critical for product launch timeline

**❓ Unresolved Questions (1):**
1. Should we also update the documentation?

**😊 Sentiment:** Positive
```

## Required Secrets
To use this agent, you must configure the following secret in the Agentverse dashboard:

- **`GOOGLE_API_KEY`**: Your Google Gemini API key
  - Get it from: https://aistudio.google.com/app/apikey
  - Sign in with your Google account
  - Click "Create API Key"
  - Copy and paste into Agentverse secrets

## Use Cases

### 1. Automated Meeting Minutes
- Automatically generate structured meeting minutes
- Extract action items without manual note-taking
- Track decisions and their rationale

### 2. Action Item Tracking
- Identify all tasks mentioned in meetings
- Assign responsibilities automatically
- Track priorities and due dates

### 3. Decision Documentation
- Record all decisions made during meetings
- Capture the reasoning behind decisions
- Maintain decision history

### 4. Team Productivity Analysis
- Analyze meeting sentiment over time
- Track participant contributions
- Identify patterns in team dynamics

### 5. Follow-up Management
- Identify unresolved questions
- Track items that need follow-up
- Ensure nothing falls through the cracks

## Integration Examples

### With Project Management Tools
Use the extracted action items to automatically create tasks in:
- Jira
- Asana
- Trello
- Linear
- Monday.com

### With Documentation Tools
Send meeting summaries to:
- Notion
- Confluence
- Google Docs
- Slack channels

### With Calendar Tools
Schedule follow-up meetings for unresolved questions

## Technical Details

- **LLM**: Google Gemini 2.5 Flash
- **Framework**: LangChain + uAgents
- **Processing**: Parallel analysis chains for efficiency
- **Output**: MCP-compatible structured data
- **Response Time**: ~5-15 seconds depending on transcript length

## Limitations

- Maximum transcript length: ~10,000 tokens (~7,500 words)
- Best results with English language transcripts
- Requires clear speaker attribution
- Works best with structured conversations

## Support

For issues or questions:
1. Check that your JSON format matches the example
2. Verify your GOOGLE_API_KEY is correctly set
3. Ensure transcript has clear speaker attribution
4. Check agent logs in Agentverse dashboard

## Version
v1.0.0 - Initial release with Gemini 2.5 Flash
