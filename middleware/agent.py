"""
AGENTVERSE DEPLOYMENT FILE - Meeting Analysis Agent
Single file for Agentverse deployment (no folder support).
Analyzes meeting transcripts using Google Gemini via LangChain + uAgents.
"""

from datetime import datetime
from uuid import uuid4
import os, json, asyncio
from typing import Dict, List, Optional, Literal
from uagents import Context, Protocol, Agent
from uagents_core.contrib.protocols.chat import (ChatAcknowledgement, ChatMessage, EndSessionContent, StartSessionContent, TextContent, chat_protocol_spec)
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# DATA MODELS
class TranscriptEntry(BaseModel):
    speaker: str; text: str; timestamp: Optional[str] = None

class MeetingInput(BaseModel):
    meeting_title: str; meeting_date: str; participants: List[str]; transcript: List[TranscriptEntry]; metadata: Optional[dict] = Field(default_factory=dict)

class ActionItem(BaseModel):
    id: str; task: str; assignee: str; priority: Literal["critical", "high", "medium", "low"]; action_type: Literal["task", "meeting", "document", "code_review", "research", "decision", "other"]; due_date: Optional[str] = None; context: str; tags: List[str] = Field(default_factory=list); mentioned_at: Optional[str] = None

class Decision(BaseModel):
    id: str; decision: str; rationale: str; involved_participants: List[str]; timestamp: Optional[str] = None; impact: Optional[str] = None; tags: List[str] = Field(default_factory=list)

class UnresolvedQuestion(BaseModel):
    id: str; question: str; asked_by: str; context: str; requires_followup: bool; timestamp: Optional[str] = None; partial_answer: Optional[str] = None

class ParticipantSummary(BaseModel):
    name: str; key_contributions: List[str]; commitments: List[str] = Field(default_factory=list); questions_asked: int = 0; speaking_time_percentage: Optional[float] = None

class MeetingSentiment(BaseModel):
    overall_tone: Literal["positive", "negative", "neutral", "mixed"]; confidence: float = Field(..., ge=0.0, le=1.0); key_indicators: List[str]; team_dynamics: Optional[str] = None

class MeetingAnalysis(BaseModel):
    meeting_id: str; meeting_title: str; meeting_date: str; analyzed_at: str; participants: List[str]; meeting_type: str; meeting_type_confidence: float; summary: str; key_topics: List[str]; action_items: List[ActionItem]; decisions: List[Decision]; unresolved_questions: List[UnresolvedQuestion]; participant_summaries: List[ParticipantSummary]; sentiment: MeetingSentiment

# PROMPTS (condensed)
MEETING_CLASSIFIER_PROMPT = ChatPromptTemplate.from_messages([("system", "Analyze meeting type, confidence (0-1), and 3-5 key topics. Return JSON."), ("user", "Meeting: {meeting_title}\nDate: {meeting_date}\nParticipants: {participants}\n\nTranscript:\n{transcript}\n\nReturn JSON: meeting_type, confidence, key_topics")])
ACTION_ITEM_EXTRACTOR_PROMPT = ChatPromptTemplate.from_messages([("system", "Extract ALL action items. CRITICAL: Use exact lowercase values:\n- priority: MUST be 'critical', 'high', 'medium', or 'low'\n- action_type: MUST be 'task', 'meeting', 'document', 'code_review', 'research', 'decision', or 'other'\n\nMapping guide:\n- Development/coding → 'task'\n- Code review → 'code_review'\n- Documentation → 'document'\n- Schedule meeting → 'meeting'\n- Research → 'research'\n- Make decision → 'decision'\n- Other → 'other'\n\nReturn JSON array with lowercase values only."), ("user", "Meeting: {meeting_title}\nParticipants: {participants}\n\nTranscript:\n{transcript}")])
DECISION_IDENTIFIER_PROMPT = ChatPromptTemplate.from_messages([("system", "Extract ALL decisions with: decision, rationale, involved_participants, timestamp, impact, tags. Return JSON array. Use lowercase for all field values."), ("user", "Meeting: {meeting_title}\nParticipants: {participants}\n\nTranscript:\n{transcript}")])
QUESTION_FLAGGING_PROMPT = ChatPromptTemplate.from_messages([("system", "Extract unresolved questions with: question, asked_by, context, requires_followup, timestamp, partial_answer. Return JSON array."), ("user", "Meeting: {meeting_title}\nParticipants: {participants}\n\nTranscript:\n{transcript}")])
PARTICIPANT_ANALYZER_PROMPT = ChatPromptTemplate.from_messages([("system", "Analyze each participant: name, key_contributions (list), commitments (list), questions_asked (INTEGER count only, not list of questions), speaking_time_percentage (float). Return JSON array."), ("user", "Meeting: {meeting_title}\nParticipants: {participants}\n\nTranscript:\n{transcript}")])
SENTIMENT_ANALYZER_PROMPT = ChatPromptTemplate.from_messages([("system", "Analyze sentiment: overall_tone (MUST be 'positive', 'negative', 'neutral', or 'mixed' - lowercase only), confidence (0.0-1.0), key_indicators (array), team_dynamics (single STRING description, not object). Return JSON with lowercase values."), ("user", "Meeting: {meeting_title}\nParticipants: {participants}\n\nTranscript:\n{transcript}")])
SUMMARY_GENERATOR_PROMPT = ChatPromptTemplate.from_messages([("system", "Create 2-3 sentence summary."), ("user", "Meeting: {meeting_title}\nType: {meeting_type}\nParticipants: {participants}\n\nTranscript:\n{transcript}\n\nAction Items: {action_items_count}\nDecisions: {decisions_count}")])

# LANGCHAIN CHAINS
class MeetingAnalysisChains:
    def __init__(self, model_name="gemini-2.5-flash", temperature=0.1, api_key=None):
        if api_key is None: api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key: raise ValueError("GOOGLE_API_KEY not found")
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=temperature, google_api_key=api_key)
        self.json_parser = JsonOutputParser()
        self.classifier_chain = ({"meeting_title": lambda x: x["meeting_title"], "meeting_date": lambda x: x["meeting_date"], "participants": lambda x: ", ".join(x["participants"]), "transcript": lambda x: self._fmt(x["transcript"])} | MEETING_CLASSIFIER_PROMPT | self.llm | self.json_parser)
        self.action_extractor_chain = ({"meeting_title": lambda x: x["meeting_title"], "participants": lambda x: ", ".join(x["participants"]), "transcript": lambda x: self._fmt(x["transcript"])} | ACTION_ITEM_EXTRACTOR_PROMPT | self.llm | self.json_parser)
        self.decision_chain = ({"meeting_title": lambda x: x["meeting_title"], "participants": lambda x: ", ".join(x["participants"]), "transcript": lambda x: self._fmt(x["transcript"])} | DECISION_IDENTIFIER_PROMPT | self.llm | self.json_parser)
        self.question_chain = ({"meeting_title": lambda x: x["meeting_title"], "participants": lambda x: ", ".join(x["participants"]), "transcript": lambda x: self._fmt(x["transcript"])} | QUESTION_FLAGGING_PROMPT | self.llm | self.json_parser)
        self.participant_chain = ({"meeting_title": lambda x: x["meeting_title"], "participants": lambda x: ", ".join(x["participants"]), "transcript": lambda x: self._fmt(x["transcript"])} | PARTICIPANT_ANALYZER_PROMPT | self.llm | self.json_parser)
        self.sentiment_chain = ({"meeting_title": lambda x: x["meeting_title"], "participants": lambda x: ", ".join(x["participants"]), "transcript": lambda x: self._fmt(x["transcript"])} | SENTIMENT_ANALYZER_PROMPT | self.llm | self.json_parser)
        self.summary_chain = ({"meeting_title": lambda x: x["meeting_title"], "meeting_type": lambda x: x.get("meeting_type", "General"), "participants": lambda x: ", ".join(x["participants"]), "transcript": lambda x: self._fmt(x["transcript"]), "action_items_count": lambda x: str(x.get("action_items_count", 0)), "decisions_count": lambda x: str(x.get("decisions_count", 0))} | SUMMARY_GENERATOR_PROMPT | self.llm)
    def _fmt(self, t): return "\n".join([f"[{e.get('timestamp','')}] {e.get('speaker','?')}: {e.get('text','')}" if e.get('timestamp') else f"{e.get('speaker','?')}: {e.get('text','')}" for e in t])
    async def classify_meeting(self, d): return await self.classifier_chain.ainvoke(d)
    async def extract_action_items(self, d): return await self.action_extractor_chain.ainvoke(d)
    async def identify_decisions(self, d): return await self.decision_chain.ainvoke(d)
    async def flag_questions(self, d): return await self.question_chain.ainvoke(d)
    async def analyze_participants(self, d): return await self.participant_chain.ainvoke(d)
    async def analyze_sentiment(self, d): return await self.sentiment_chain.ainvoke(d)
    async def generate_summary(self, d): r = await self.summary_chain.ainvoke(d); return r.content if hasattr(r, 'content') else str(r)

# MEETING ANALYSIS AGENT
class MeetingAnalysisAgent:
    def __init__(self, model_name="gemini-2.5-flash", temperature=0.1, api_key=None):
        self.chains = MeetingAnalysisChains(model_name, temperature, api_key)
    
    def _normalize_priority(self, priority) -> str:
        """Normalize priority to lowercase and validate."""
        if not isinstance(priority, str): return "medium"
        priority = priority.lower().strip()
        return priority if priority in ["critical", "high", "medium", "low"] else "medium"
    
    def _normalize_action_type(self, action_type) -> str:
        """Map action_type to valid values."""
        if not isinstance(action_type, str): return "task"
        action_type = action_type.lower().strip()
        mapping = {"development": "task", "coding": "task", "implementation": "task", "programming": "task", "review": "code_review", "code review": "code_review", "documentation": "document", "docs": "document", "doc": "document", "meeting": "meeting", "research": "research", "decision": "decision"}
        action_type = mapping.get(action_type, action_type)
        return action_type if action_type in ["task", "meeting", "document", "code_review", "research", "decision", "other"] else "task"
    
    def _normalize_mentioned_at(self, mentioned_at):
        """Convert mentioned_at to string if it's a list."""
        if isinstance(mentioned_at, list): return mentioned_at[0] if mentioned_at else None
        return mentioned_at if isinstance(mentioned_at, str) else None
    
    def _normalize_sentiment_tone(self, tone) -> str:
        """Normalize sentiment tone to lowercase and validate."""
        if not isinstance(tone, str): return "neutral"
        tone = tone.lower().strip()
        return tone if tone in ["positive", "negative", "neutral", "mixed"] else "neutral"
    
    def _normalize_questions_asked(self, questions_asked) -> int:
        """Normalize questions_asked to integer count."""
        try:
            if isinstance(questions_asked, int): return questions_asked
            if isinstance(questions_asked, list): return len(questions_asked)
            if isinstance(questions_asked, str): return int(questions_asked)
            return 0
        except Exception:
            return 0
    
    def _normalize_team_dynamics(self, team_dynamics) -> Optional[str]:
        """Normalize team_dynamics to a simple string."""
        try:
            if isinstance(team_dynamics, str): return team_dynamics
            if isinstance(team_dynamics, dict):
                parts = []
                for key, value in team_dynamics.items():
                    if isinstance(value, str): parts.append(f"{key}: {value}")
                return "; ".join(parts) if parts else None
            return None
        except Exception:
            return None
    
    async def analyze_meeting(self, meeting_input: Dict) -> Dict:
        validated_input = MeetingInput(**meeting_input)
        input_dict = validated_input.model_dump()
        results = await asyncio.gather(self.chains.classify_meeting(input_dict), self.chains.extract_action_items(input_dict), self.chains.identify_decisions(input_dict), self.chains.flag_questions(input_dict), self.chains.analyze_participants(input_dict), self.chains.analyze_sentiment(input_dict), return_exceptions=True)
        classification, action_items_raw, decisions_raw, questions_raw, participants_raw, sentiment_raw = [r if not isinstance(r, Exception) else ({} if i in [0,5] else []) for i, r in enumerate(results)]
        summary_input = {**input_dict, "meeting_type": classification.get("meeting_type", "General"), "action_items_count": len(action_items_raw), "decisions_count": len(decisions_raw)}
        summary = await self.chains.generate_summary(summary_input)
        meeting_id = str(uuid4())
        action_items = [ActionItem(id=it.get("id", f"action_{i+1}"), task=it.get("task", ""), assignee=it.get("assignee", "Unassigned"), priority=self._normalize_priority(it.get("priority", "medium")), action_type=self._normalize_action_type(it.get("action_type", "task")), due_date=it.get("due_date"), context=it.get("context", ""), tags=it.get("tags", []), mentioned_at=self._normalize_mentioned_at(it.get("mentioned_at"))) for i, it in enumerate(action_items_raw) if it.get("task")]
        decisions = [Decision(id=it.get("id", f"decision_{i+1}"), decision=it.get("decision", ""), rationale=it.get("rationale", ""), involved_participants=it.get("involved_participants", []), timestamp=it.get("timestamp"), impact=it.get("impact"), tags=it.get("tags", [])) for i, it in enumerate(decisions_raw) if it.get("decision")]
        questions = [UnresolvedQuestion(id=it.get("id", f"question_{i+1}"), question=it.get("question", ""), asked_by=it.get("asked_by", "Unknown"), context=it.get("context", ""), requires_followup=it.get("requires_followup", True), timestamp=it.get("timestamp"), partial_answer=it.get("partial_answer")) for i, it in enumerate(questions_raw) if it.get("question")]
        participant_summaries = [ParticipantSummary(name=it.get("name", "Unknown"), key_contributions=it.get("key_contributions", []), commitments=it.get("commitments", []), questions_asked=self._normalize_questions_asked(it.get("questions_asked", 0)), speaking_time_percentage=it.get("speaking_time_percentage")) for it in participants_raw if it.get("name")]
        sentiment = MeetingSentiment(overall_tone=self._normalize_sentiment_tone(sentiment_raw.get("overall_tone", "neutral")), confidence=sentiment_raw.get("confidence", 0.5), key_indicators=sentiment_raw.get("key_indicators", []), team_dynamics=self._normalize_team_dynamics(sentiment_raw.get("team_dynamics")))
        analysis = MeetingAnalysis(meeting_id=meeting_id, meeting_title=validated_input.meeting_title, meeting_date=validated_input.meeting_date, analyzed_at=datetime.utcnow().isoformat(), participants=validated_input.participants, meeting_type=classification.get("meeting_type", "General"), meeting_type_confidence=classification.get("confidence", 0.8), summary=summary, key_topics=classification.get("key_topics", []), action_items=action_items, decisions=decisions, unresolved_questions=questions, participant_summaries=participant_summaries, sentiment=sentiment)
        return analysis.model_dump()

# UAGENTS SETUP
def create_text_chat(text: str, end_session: bool = False) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    if end_session: content.append(EndSessionContent(type="end-session"))
    return ChatMessage(timestamp=datetime.utcnow(), msg_id=uuid4(), content=content)

agent = Agent(name="MeetingAnalysisAgent", seed="meeting_analysis_agent_seed_v1")
protocol = Protocol(spec=chat_protocol_spec)
my_langchain_agent_instance = None
try:
    if os.getenv("GOOGLE_API_KEY"): my_langchain_agent_instance = MeetingAnalysisAgent(); print("✅ Agent initialized for local testing!")
    else: print("⚠️  Will initialize with Agentverse secrets on first message")
except Exception as e: print(f"❌ Error: {e}")

@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id))
    if any(isinstance(item, StartSessionContent) for item in msg.content):
        await ctx.send(sender, create_text_chat("Hello! Send me a meeting transcript in JSON format.\n\nExample: {\"meeting_title\": \"Sprint Planning\", \"meeting_date\": \"2024-10-25T14:00:00Z\", \"participants\": [\"Alice\", \"Bob\"], \"transcript\": [{\"speaker\": \"Alice\", \"text\": \"Let's discuss the roadmap\", \"timestamp\": \"14:00:00\"}]}", end_session=False))
        return
    user_text = msg.text()
    if not user_text: return
    ctx.logger.info(f"Received message: {user_text[:100]}...")
    global my_langchain_agent_instance
    if my_langchain_agent_instance is None:
        try:
            google_api_key = ctx.storage.get("GOOGLE_API_KEY")
            if not google_api_key: await ctx.send(sender, create_text_chat("❌ GOOGLE_API_KEY not configured in secrets", end_session=True)); return
            my_langchain_agent_instance = MeetingAnalysisAgent(api_key=google_api_key)
            ctx.logger.info("✅ Agent initialized with secrets")
        except Exception as e: await ctx.send(sender, create_text_chat(f"❌ Init failed: {e}", end_session=True)); return
    try:
        try: meeting_input = json.loads(user_text)
        except json.JSONDecodeError: await ctx.send(sender, create_text_chat("❌ Invalid JSON format", end_session=True)); return
        ctx.logger.info(f"Processing: {meeting_input.get('meeting_title', '?')}")
        result = await my_langchain_agent_instance.analyze_meeting(meeting_input)
        output = [f"📊 **{result.get('meeting_title')}**\n", f"📅 {result.get('meeting_date')}", f"🏷️  {result.get('meeting_type')}\n", f"**Summary:**\n{result.get('summary')}\n"]
        action_items = result.get('action_items', [])
        if action_items:
            output.append(f"**✅ Action Items ({len(action_items)}):**")
            for i, it in enumerate(action_items, 1): output.append(f"{i}. **{it.get('task')}** - {it.get('assignee')} ({it.get('priority')})")
            output.append("")
        decisions = result.get('decisions', [])
        if decisions:
            output.append(f"**🎯 Decisions ({len(decisions)}):**")
            for i, d in enumerate(decisions, 1): output.append(f"{i}. {d.get('decision')}")
            output.append("")
        questions = result.get('unresolved_questions', [])
        if questions:
            output.append(f"**❓ Questions ({len(questions)}):**")
            for i, q in enumerate(questions, 1): output.append(f"{i}. {q.get('question')}")
            output.append("")
        sentiment = result.get('sentiment', {})
        if sentiment: output.append(f"**😊 Sentiment:** {sentiment.get('overall_tone', 'neutral').capitalize()}")
        await ctx.send(sender, create_text_chat("\n".join(output), end_session=True))
    except Exception as e: ctx.logger.exception(f"Error: {e}"); await ctx.send(sender, create_text_chat(f"❌ Error: {e}", end_session=True))

@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement): pass

agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    print("🚀 Starting MeetingAnalysisAgent locally...")
    print("🔑 Make sure GOOGLE_API_KEY is set!")
    print("="*80)
    agent.run()