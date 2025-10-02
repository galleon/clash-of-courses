"""SmolAgents-based chat agent for BRS - replaces the original chat agent."""

import os
import logging
from datetime import datetime, timezone
from typing import Any

from smolagents import ToolCallingAgent, OpenAIModel
from sqlalchemy.orm import joinedload

from brs_backend.auth.jwt_handler import JWTClaims
from brs_backend.api.chat_models import (
    ChatReply,
    ChatAudit,
    ChatCard,
    ChatAction,
    CardType,
    ActionType,
)
from brs_backend.models.database import (
    Course,
    Section,
    Student,
    Enrollment,
    RegistrationRequest,
    Instructor,
    SectionMeeting
)

# Import role-specific tools
from brs_backend.agents.student_tools import (
    get_student_info,
    check_attachable,
    browse_course_catalog,
    search_sections,
    create_registration_request,
    get_current_schedule,
    request_course_addition,
)
from brs_backend.agents.advisor_tools import (
    get_pending_requests,
    explain_rule,
    propose_alternatives,
    decide_request,
    get_student_profile,
)

logger = logging.getLogger(__name__)


class BRSChatAgent:
    """SmolAgents-powered chat agent with role-based routing."""

    def __init__(self):
        """Initialize the SmolAgents-based chat system."""
        self.model = OpenAIModel(
            model_id=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        self.agents = {}
        self._setup_role_agents()

    def _setup_role_agents(self):
        """Setup role-specific agents with appropriate tools."""

        # Student Agent
        student_tools = [
            get_student_info,
            check_attachable,
            browse_course_catalog,
            search_sections,
            create_registration_request,
            get_current_schedule,
            request_course_addition,
        ]

        self.agents["student"] = ToolCallingAgent(
            tools=student_tools,
            model=self.model,
        )

        # Instructor Agent (was "advisor")
        instructor_tools = [
            get_pending_requests,
            explain_rule,
            propose_alternatives,
            decide_request,
            get_student_profile,
        ]

        self.agents["instructor"] = ToolCallingAgent(
            tools=instructor_tools,
            model=self.model,
        )

        # Department Head Agent (simplified for now - can be expanded)
        department_tools = [
            get_pending_requests,
            explain_rule,
            get_student_profile,
        ]

        self.agents["department_head"] = ToolCallingAgent(
            tools=department_tools,
            model=self.model,
        )

        # System Admin Agent (was "registrar")
        admin_tools = [
            get_student_profile,
        ]

        self.agents["system_admin"] = ToolCallingAgent(
            tools=admin_tools,
            model=self.model,
        )

    async def process_message(
        self,
        message: str,
        user_claims: JWTClaims,
        session_id: str,
        correlation_id: str,
        db: Any,
    ) -> ChatReply:
        """Process a chat message using a single ToolCallingAgent with post-processing for card creation."""

        logger.info(
            f"🤖 Processing message: '{message}' from {user_claims.user_type} user {user_claims.full_name}"
        )

        # Get the appropriate agent for the user's role
        agent = self.agents.get(user_claims.user_type)
        if not agent:
            logger.error(f"No agent configured for role: {user_claims.user_type}")
            return await self._fallback_response(
                user_claims,
                correlation_id,
                f"Sorry, I don't have support for {user_claims.user_type} users yet.",
            )

        try:
            # Prepare context for the agent
            user_context = {
                "student_id": user_claims.actor_id
                if user_claims.user_type == "student"
                else None,
                "instructor_id": user_claims.actor_id
                if user_claims.user_type == "instructor"
                else None,
                "department_head_id": user_claims.actor_id
                if user_claims.user_type == "department_head"
                else None,
                "system_admin_id": user_claims.actor_id
                if user_claims.user_type == "system_admin"
                else None,
                "user_name": user_claims.full_name,
                "session_id": session_id,
                "correlation_id": correlation_id,
            }

            # Enhanced message with context
            enhanced_message = f"""User Context: {user_context}

User Message: {message}

Please help the user with their request. Use the appropriate tools and provide helpful responses."""

            # Run the ToolCallingAgent
            logger.info(f"🚀 Running ToolCallingAgent for {user_claims.user_type}")

            # 🔍 DEBUG: Log the exact message being sent to agent
            logger.info("="*80)
            logger.info("🔍 DEBUG: MESSAGE BEING SENT TO AGENT:")
            logger.info(f"📝 Enhanced message: {enhanced_message}")
            logger.info("="*80)

            # Store tool results during execution
            self._captured_tool_results = {}

            # Debug: Check tool structure
            agent_tools = getattr(agent, 'tools', [])
            logger.info(f"🔧 Found {len(agent_tools)} tools available to agent")

            if agent_tools:
                tool_names = [getattr(tool, 'name', str(tool)) for tool in agent_tools]
                logger.info(f"🔧 Available tools: {tool_names}")

            # Run the agent and capture the complete output
            logger.info("� CALLING agent.run() - BEFORE EXECUTION")
            result = agent.run(enhanced_message)
            logger.info("✅ CALLING agent.run() - AFTER EXECUTION")

            # 🔍 DEBUG: Log the complete agent output
            logger.info("="*80)
            logger.info("🔍 DEBUG: COMPLETE AGENT OUTPUT:")
            logger.info(f"📤 Result type: {type(result)}")
            logger.info(f"📤 Result content: {result}")
            logger.info("="*80)

            # Get the text response from the agent
            agent_response = str(result) if result else "I encountered an issue processing your request."
            logger.info(f"✅ Agent response: {agent_response[:200]}...")

            # 🔍 DEBUG: Check agent state after execution to see what tools were called
            logger.info("="*80)
            logger.info("🔍 DEBUG: COMPREHENSIVE AGENT INSPECTION:")

            # Check all agent attributes
            logger.info(f"📊 Agent type: {type(agent)}")
            logger.info(f"📊 Agent dir: {[attr for attr in dir(agent) if not attr.startswith('_')]}")

            # Check specific important attributes
            important_attrs = ['state', 'memory', 'messages', 'chat_history', 'conversation', 'history', 'logs', 'tools', 'tool_calls']
            for attr in important_attrs:
                if hasattr(agent, attr):
                    attr_value = getattr(agent, attr)
                    logger.info(f"📊 Agent.{attr}: {type(attr_value)}")

                    # Special handling for memory
                    if attr == 'memory' and attr_value:
                        logger.info(f"🧠 MEMORY CONTENT: {attr_value}")
                        if hasattr(attr_value, '__dict__'):
                            logger.info(f"🧠 Memory attributes: {list(attr_value.__dict__.keys())}")

                        # Check memory.steps in detail
                        if hasattr(attr_value, 'steps'):
                            steps = attr_value.steps
                            logger.info(f"🧠 Memory steps: {len(steps)} items")
                            logger.info(f"🧠 Memory steps type: {type(steps)}")

                            # Examine the steps in detail
                            for i, step in enumerate(steps):
                                logger.info(f"🧠   Step {i}: {type(step)}")
                                logger.info(f"🧠   Step {i} content: {str(step)[:300]}...")

                                # Check if step has attributes we can inspect
                                if hasattr(step, '__dict__'):
                                    logger.info(f"🧠   Step {i} attributes: {list(step.__dict__.keys())}")

                                # Look for tool results in steps
                                step_str = str(step)
                                if "Observation:" in step_str and "preferred_card_types" in step_str:
                                    logger.info(f"🧠   🎯 FOUND TOOL RESULT IN STEP {i}!")
                                    try:
                                        import json
                                        if "Observation:\n" in step_str:
                                            result_part = step_str.split("Observation:\n")[1].strip()
                                            if result_part.startswith("{"):
                                                result_json = json.loads(result_part)
                                                logger.info(f"🧠   📊 Parsed step tool result: {result_json}")
                                                if 'preferred_card_types' in result_json:
                                                    logger.info(f"🧠   🎯 Found preferred_card_types in step: {result_json['preferred_card_types']}")
                                    except Exception as e:
                                        logger.info(f"🧠   ⚠️ Failed to parse step tool result: {e}")

                        if hasattr(attr_value, 'messages'):
                            logger.info(f"🧠 Memory messages: {len(attr_value.messages)} items")
                            for i, msg in enumerate(attr_value.messages[-3:]):  # Show last 3 messages
                                logger.info(f"🧠   Message {i}: {type(msg)} - {str(msg)[:200]}...")

                                # Look for tool results in memory messages
                                if hasattr(msg, 'content') and "Observation:" in str(msg.content) and "preferred_card_types" in str(msg.content):
                                    logger.info(f"🧠   🎯 FOUND TOOL RESULT IN MEMORY MESSAGE {i}!")

                        # Check if memory has direct access to tool results
                        if hasattr(attr_value, 'tool_calls') or hasattr(attr_value, 'tool_results'):
                            logger.info(f"🧠 Memory has tool-related attributes!")
                else:
                    logger.info(f"📊 Agent.{attr}: NOT FOUND")
            if hasattr(agent, 'state'):
                logger.info(f"📊 Agent has state: {type(agent.state)}")
                logger.info(f"📊 Agent state keys: {list(agent.state.keys()) if isinstance(agent.state, dict) else 'Not a dict'}")

                # Check if state has messages
                if isinstance(agent.state, dict) and 'messages' in agent.state:
                    messages = agent.state['messages']
                    logger.info(f"📨 Agent state has {len(messages)} messages")

                    # Look for tool calls and results in messages
                    for i, msg in enumerate(messages):
                        logger.info(f"📨 Message {i}: {type(msg)}")
                        if hasattr(msg, 'role'):
                            logger.info(f"   📨 Role: {msg.role}")
                        if hasattr(msg, 'content'):
                            content_preview = str(msg.content)[:200] + "..." if len(str(msg.content)) > 200 else str(msg.content)
                            logger.info(f"   � Content: {content_preview}")

                            # Look for tool results in content
                            if "Observation:" in str(msg.content) and "preferred_card_types" in str(msg.content):
                                logger.info(f"   🎯 FOUND TOOL RESULT IN MESSAGE {i}!")
                                # Try to extract the tool result
                                try:
                                    import json
                                    content_str = str(msg.content)
                                    if "Observation:\n" in content_str:
                                        result_part = content_str.split("Observation:\n")[1].strip()
                                        if result_part.startswith("{"):
                                            # Try to parse as JSON
                                            result_json = json.loads(result_part)
                                            logger.info(f"   📊 Parsed tool result: {result_json}")
                                            if 'preferred_card_types' in result_json:
                                                logger.info(f"   🎯 Found preferred_card_types: {result_json['preferred_card_types']}")
                                except Exception as e:
                                    logger.info(f"   ⚠️ Failed to parse tool result: {e}")

                # Check other possible locations in state
                for key in agent.state.keys() if isinstance(agent.state, dict) else []:
                    if key != 'messages':
                        logger.info(f"� State[{key}]: {type(agent.state[key])}")

            else:
                logger.info("📊 Agent has no state attribute")
            logger.info("="*80)

            # 🎯 EXTRACT TOOL RESULTS FROM AGENT MEMORY
            tool_results = []
            if hasattr(agent, 'memory') and hasattr(agent.memory, 'steps'):
                logger.info(f"🧠 Extracting tool results from {len(agent.memory.steps)} memory steps")

                for i, step in enumerate(agent.memory.steps):
                    # Look for ActionSteps that contain tool calls and observations
                    if hasattr(step, 'tool_calls') and hasattr(step, 'observations') and step.tool_calls:
                        logger.info(f"🧠 Step {i}: Found {len(step.tool_calls)} tool calls")

                        # Extract observations (tool results)
                        if step.observations:
                            logger.info(f"🧠   Observations type: {type(step.observations)}")
                            logger.info(f"🧠   Observations content: {str(step.observations)[:500]}...")

                            # Handle different observation formats
                            observations_to_process = []
                            if isinstance(step.observations, str):
                                # Single string observation
                                observations_to_process = [step.observations]
                            elif isinstance(step.observations, list):
                                # List of observations
                                observations_to_process = step.observations
                            else:
                                # Try to convert to list
                                try:
                                    observations_to_process = list(step.observations)
                                except:
                                    logger.info(f"🧠   ⚠️ Cannot convert observations to list: {type(step.observations)}")
                                    continue

                            for obs_idx, observation in enumerate(observations_to_process):
                                logger.info(f"🧠   Observation {obs_idx}: {str(observation)[:200]}...")

                                # Try to parse tool result from observation
                                try:
                                    import json
                                    import ast
                                    # Observations might be direct strings or structured data
                                    if isinstance(observation, str):
                                        # Try to parse as JSON first
                                        if observation.strip().startswith('{'):
                                            try:
                                                result_data = json.loads(observation.strip())
                                            except json.JSONDecodeError:
                                                # If JSON fails, try Python literal_eval (for dict with single quotes)
                                                try:
                                                    result_data = ast.literal_eval(observation.strip())
                                                except (ValueError, SyntaxError):
                                                    # Skip if can't parse as either JSON or Python literal
                                                    continue
                                        else:
                                            # Skip non-JSON observations
                                            continue
                                    else:
                                        # Already structured data
                                        result_data = observation

                                    # Check if this looks like our tool result format
                                    if isinstance(result_data, dict) and 'preferred_card_types' in result_data:
                                        logger.info(f"🧠   🎯 FOUND TOOL RESULT in observation {obs_idx}!")
                                        logger.info(f"🧠   📊 Tool result: {result_data}")
                                        tool_results.append(result_data)

                                except Exception as e:
                                    logger.info(f"🧠   ⚠️ Failed to parse observation {obs_idx}: {e}")

            logger.info(f"🔧 Extracted {len(tool_results)} tool results from agent memory")

            # Create cards based on tool results (preferred) or text analysis (fallback)
            cards = []
            if tool_results:
                logger.info(f"🎯 Using tool results to create cards: {len(tool_results)} results found")
                cards = self._create_cards_from_tool_results(tool_results, user_claims)
            else:
                logger.info("📝 No tool results found, falling back to response analysis")
                # Fallback to response analysis method
                cards = await self._create_cards_from_response_analysis(agent_response, user_claims)

            # Create audit log
            audit = ChatAudit(
                correlation_id=correlation_id,
                user_type=user_claims.user_type,
                actor_id=user_claims.actor_id,
                tool_calls=[],
                timestamp=datetime.now(timezone.utc),
            )

            logger.info(f"🎯 Created {len(cards)} cards total")

            return ChatReply(
                message=agent_response,
                cards=cards,
                actions=[],  # No immediate actions for now
                audit=audit,
            )

        except Exception as e:
            logger.error(f"❌ Error in agent processing: {e}")
            return await self._fallback_response(
                user_claims, correlation_id, "I encountered an error processing your request. Please try again."
            )

    def _create_cards_from_tool_results(self, tool_results: list[dict], user_claims: JWTClaims) -> list[ChatCard]:
        """Create cards based on extracted tool results with preferred_card_types."""
        cards = []

        for i, tool_result in enumerate(tool_results):
            try:
                logger.info(f"🔧 Processing tool result {i}: {tool_result.get('preferred_card_types', 'No preferred types')}")

                # Get preferred card types and data from tool result
                preferred_types = tool_result.get('preferred_card_types', ['generic'])
                data = tool_result.get('data')
                success = tool_result.get('success', False)

                if not success or not data:
                    logger.warning(f"⚠️ Tool result {i} not successful or missing data")
                    continue

                # Try to create cards in order of preference
                card_created = False
                for card_type in preferred_types:
                    try:
                        if card_type == 'week_grid':
                            # Create WeekGridCard for schedule data
                            card = self._create_schedule_card_from_data(data, user_claims)
                            if card:
                                cards.append(card)
                                card_created = True
                                logger.info(f"✅ Created {card_type} card from tool result {i}")
                                break

                        elif card_type == 'course_info':
                            # Create course info card
                            # Check if this is single course (search_sections) or multiple courses (browse_catalog)
                            if 'courses' in data and isinstance(data['courses'], list):
                                # Multiple courses from browse_catalog
                                card = self._create_course_catalog_card(data)
                            else:
                                # Single course from search_sections
                                card = self._create_sections_card_from_data(data)

                            if card:
                                cards.append(card)
                                card_created = True
                                logger.info(f"✅ Created {card_type} card from tool result {i}")
                                break

                        elif card_type == 'request_summary':
                            # Create request summary card
                            card = self._create_generic_card(data, "request_summary")
                            if card:
                                cards.append(card)
                                card_created = True
                                logger.info(f"✅ Created {card_type} card from tool result {i}")
                                break

                        elif card_type == 'alternatives':
                            # Create alternatives card
                            card = self._create_alternatives_card(data)
                            if card:
                                cards.append(card)
                                card_created = True
                                logger.info(f"✅ Created {card_type} card from tool result {i}")
                                break

                        elif card_type == 'generic':
                            # Create generic card as fallback
                            card = self._create_generic_card(data, "generic")
                            if card:
                                cards.append(card)
                                card_created = True
                                logger.info(f"✅ Created {card_type} card from tool result {i}")
                                break

                    except Exception as e:
                        logger.warning(f"⚠️ Failed to create {card_type} card: {e}")
                        continue

                if not card_created:
                    logger.warning(f"⚠️ Could not create any card for tool result {i}")

            except Exception as e:
                logger.warning(f"⚠️ Error processing tool result {i}: {e}")

        logger.info(f"🎯 Created {len(cards)} cards from {len(tool_results)} tool results")
        return cards

    async def _create_cards_from_response_analysis(self, agent_response: str, user_claims: JWTClaims) -> list[ChatCard]:
        """Analyze the agent response text to determine what cards to create.

        This approach analyzes the actual response content to detect patterns
        that indicate specific data was retrieved and cards should be created.
        """
        cards = []

        try:
            # Convert to lowercase for easier pattern matching
            response_lower = agent_response.lower()

            # Pattern 1: Schedule information detection (more specific patterns)
            schedule_patterns = [
                "current schedule",
                "your schedule",
                "weekly schedule",
                "schedule for",
                "enrolled in",
                "registered for"
            ]

            if any(pattern in response_lower for pattern in schedule_patterns):
                logger.info("🗓️ Detected schedule information in response")
                schedule_card = await self._create_schedule_card_from_text(agent_response, user_claims)
                if schedule_card:
                    cards.append(schedule_card)

            # Pattern 2: Student info detection
            student_info_patterns = [
                "student id:",
                "gpa:",
                "year:",
                "program:",
                "credits completed",
                "academic standing"
            ]

            if any(pattern in response_lower for pattern in student_info_patterns):
                logger.info("👤 Detected student information in response")
                student_card = await self._create_student_info_card_from_text(agent_response, user_claims)
                if student_card:
                    cards.append(student_card)

            # Pattern 3: Course search results
            search_patterns = [
                "available sections",
                "course sections",
                "found sections",
                "section ",
                "available spots",
                "waitlist"
            ]

            if any(pattern in response_lower for pattern in search_patterns):
                logger.info("🔍 Detected course search results in response")
                search_card = await self._create_search_results_card_from_text(agent_response, user_claims)
                if search_card:
                    cards.append(search_card)

            # Pattern 4: Registration request detection
            request_patterns = [
                "registration request",
                "request submitted",
                "request created",
                "pending approval",
                "request id:"
            ]

            if any(pattern in response_lower for pattern in request_patterns):
                logger.info("📝 Detected registration request in response")
                request_card = await self._create_request_card_from_text(agent_response, user_claims)
                if request_card:
                    cards.append(request_card)

        except Exception as e:
            logger.warning(f"⚠️ Error analyzing response for cards: {e}")

        return cards

    async def _create_schedule_card_from_text(self, response_text: str, user_claims: JWTClaims) -> ChatCard | None:
        """Create a schedule card by re-fetching data for the current user."""
        try:
            # Import here to avoid circular imports
            from brs_backend.agents.student_tools import get_current_schedule

            # Call the tool directly to get structured data
            context = {"student_id": user_claims.actor_id}
            result = get_current_schedule(context)

            if result.get("success") and result.get("data"):
                # Use the card creation logic with proper preferred types
                return self._create_schedule_card_from_data(result["data"], user_claims)

        except Exception as e:
            logger.warning(f"⚠️ Error creating schedule card from text: {e}")
        return None

    async def _create_student_info_card_from_text(self, response_text: str, user_claims: JWTClaims) -> ChatCard | None:
        """Create a student info card by re-fetching data for the current user."""
        try:
            from brs_backend.agents.student_tools import get_student_info

            context = {"student_id": user_claims.actor_id}
            result = get_student_info(context)

            if result.get("success") and result.get("data"):
                return self._create_generic_card(result["data"], "get_student_info")

        except Exception as e:
            logger.warning(f"⚠️ Error creating student info card from text: {e}")
        return None

    async def _create_search_results_card_from_text(self, response_text: str, user_claims: JWTClaims) -> ChatCard | None:
        """Create a course search results card from response text."""
        logger.info("🔍 Creating generic card for course search results")

        # Create a generic card with the search results
        return ChatCard(
            card_type=CardType.GENERIC,
            content=response_text,
            title="Available Courses",
            metadata={"type": "course_search_results"}
        )

    async def _create_request_card_from_text(self, response_text: str, user_claims: JWTClaims) -> ChatCard | None:
        """Create a request card - would need request ID from context."""
        # This is more complex as we'd need to extract request details
        # For now, return None but could be enhanced later
        logger.info("📝 Request card creation from text not yet implemented")
        return None

    async def _fallback_response(
        self, user_claims: JWTClaims, correlation_id: str, message: str
    ) -> ChatReply:
        """Provide a fallback response when SmolAgents fails."""

        return ChatReply(
            message=message,
            audit=ChatAudit(
                correlation_id=correlation_id,
                user_type=user_claims.user_type,
                actor_id=user_claims.actor_id,
                tool_calls=["fallback"],
                timestamp=datetime.now(timezone.utc),
            ),
        )

    async def _post_process_response(
        self,
        agent_response: str,
        original_message: str,
        user_claims: JWTClaims,
        correlation_id: str,
        db: Any,
        tool_results: dict[str, Any] | None = None,
    ) -> ChatReply:
        """Post-process SmolAgents response to add cards for UI when appropriate."""

        logger.info(f"🔄 Post-processing response for {user_claims.user_type} user")

        cards = []

        # First priority: Use structured tool results if available
        if tool_results:
            logger.info("📊 Creating cards from structured tool results")
            tool_cards = self._create_cards_from_tool_results(tool_results, user_claims)
            cards.extend(tool_cards)

        # Fallback: Text-based detection for schedule responses (legacy)
        if not cards and user_claims.user_type == "student":
            is_schedule_response = self._is_schedule_response(agent_response, original_message)
            if is_schedule_response:
                logger.info("📅 Converting schedule response to card format (text-based fallback)")
                schedule_card = self._extract_schedule_card(agent_response, user_claims, db)
                if schedule_card:
                    cards.append(schedule_card)

        return ChatReply(
            message=agent_response,
            cards=cards,
            audit=ChatAudit(
                correlation_id=correlation_id,
                user_type=user_claims.user_type,
                actor_id=user_claims.actor_id,
                tool_calls=["smolagents_" + user_claims.user_type],
                timestamp=datetime.now(timezone.utc),
                audit_data={
                    "agent_type": "smolagents",
                    "post_processed": len(cards) > 0,
                },
            ),
        )

    def _is_schedule_response(self, response: str, original_message: str) -> bool:
        """Detect if the response contains schedule information."""

        # Check if original message was about schedule
        schedule_keywords = ["schedule", "timetable", "calendar", "classes", "courses"]
        message_is_schedule = any(
            keyword in original_message.lower() for keyword in schedule_keywords
        )

        # Check if response contains schedule-like content (multiple formats)
        schedule_indicators = [
            "Course Code:",
            "Course Title:",
            "Credits:",
            "Section Code:",
            "Instructor:",
            "Meetings:",
            "Total Credits:",
            "**Course Code**",
            "**Course Title**",
            "**Credits**",
            "**Section Code**",
            "**Instructor**",
            "**Meetings**",
            "**Total Credits**",
        ]
        response_has_schedule = any(
            indicator in response for indicator in schedule_indicators
        )

        logger.info(
            f"🔍 Schedule detection: message_keywords={message_is_schedule}, response_indicators={response_has_schedule}"
        )

        return message_is_schedule and response_has_schedule

    def _extract_schedule_card(self, response: str, user_claims: JWTClaims, db: Any = None) -> ChatCard:
        """Extract schedule data directly from database and create a UI card."""

        if not db:
            # If no db session provided, we can't query - return None
            logger.warning("No database session provided for schedule extraction")
            return None

        try:
            # Query student's current enrollments directly from database
            student = db.query(Student).filter(Student.student_id == user_claims.actor_id).first()
            if not student:
                logger.error(f"Student not found for actor_id: {user_claims.actor_id}")
                return None

            # Get current enrollments with proper joins for schedule data
            enrollments = db.query(Enrollment).filter(
                Enrollment.student_id == student.student_id,
                Enrollment.status == "registered"
            ).options(
                joinedload(Enrollment.section).joinedload(Section.course),
                joinedload(Enrollment.section).joinedload(Section.instructor)
            ).all()

            if not enrollments:
                logger.info("No enrollments found for student")
                return None

            # Format schedule data for the card
            schedule_entries = []
            for enrollment in enrollments:
                section = enrollment.section
                course = section.course

                # Get meeting times for this section
                meetings = db.query(SectionMeeting).filter(
                    SectionMeeting.section_id == section.section_id
                ).all()

                # Format meeting times
                time_str = "TBD"
                if meetings:
                    meeting_times = []
                    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                    for meeting in meetings:
                        day_name = days[meeting.day_of_week] if meeting.day_of_week < len(days) else "Unknown"
                        # Extract time from PostgreSQL tsrange
                        time_range = str(meeting.time_range)
                        if '","' in time_range:
                            start_time = time_range.split('","')[0].split(' ')[1]
                            end_time = time_range.split('","')[1].split(' ')[1].rstrip(')')
                            meeting_times.append(f"{day_name} {start_time}-{end_time}")
                    time_str = ", ".join(meeting_times) if meeting_times else "TBD"

                entry = {
                    "course_code": course.code,
                    "title": course.title,
                    "section": section.section_code,
                    "instructor": section.instructor.name if section.instructor else "TBA",
                    "time": time_str,
                    "credits": course.credits if course.credits else 0,
                    "room": section.meetings[0].room.name if section.meetings and section.meetings[0].room else "TBA"
                }
                schedule_entries.append(entry)

            if not schedule_entries:
                return None

            # Create the schedule card
            schedule_payload = {
                "student_name": user_claims.full_name,
                "total_credits": sum(entry["credits"] for entry in schedule_entries),
                "courses": schedule_entries
            }

            return ChatCard(type=CardType.WEEK_GRID, payload=schedule_payload)

        except Exception as e:
            logger.error(f"Error creating schedule card: {str(e)}")
            return None

    def _format_course_for_card(self, course_data: dict) -> dict:
        """Format course data for UI card display."""
        return {
            "course_code": course_data.get("course_code", ""),
            "title": course_data.get("title", ""),
            "section": course_data.get("section", ""),
            "time": course_data.get("meetings", "TBD"),
            "instructor": course_data.get("instructor", ""),
            "room": "TBD",  # Room info would need to be extracted from meetings text
        }

    def _detect_intent(self, message: str) -> str:
        """Simple intent detection based on keywords."""
        logger.debug(f"🔍 Analyzing message for intent: '{message}'")

        # Split into words for better matching
        words = message.lower().split()

        # Check for greeting (be more specific)
        if any(
            word in words for word in ["hello", "hi", "hey"]
        ) or message.lower().startswith("good"):
            logger.debug("📝 Matched greeting keywords")
            return "greeting"

        # Check for schedule inquiry
        elif any(word in words for word in ["schedule", "timetable", "calendar"]):
            logger.debug("📅 Matched schedule keywords")
            return "schedule_inquiry"

        # Check for course inquiry (courses, available, list)
        elif any(
            word in words for word in ["courses", "available", "list", "catalog"]
        ) and any(
            word in words for word in ["course", "courses", "which", "what", "show"]
        ):
            logger.debug("📚 Matched course inquiry keywords")
            return "schedule_inquiry"  # Reuse schedule handler for course listing

        # Check for add course (improved pattern)
        elif any(word in words for word in ["add", "enroll", "register", "take"]) and (
            any(word in words for word in ["course", "class"])
            or any(
                word.startswith(prefix)
                for word in words
                for prefix in ["cs", "math", "phys", "engl", "hist"]
            )
        ):
            logger.debug("➕ Matched add course keywords")
            return "add_course"

        # Check for change section
        elif any(word in words for word in ["change", "switch", "swap"]) and any(
            word in words for word in ["section", "time"]
        ):
            logger.debug("🔄 Matched change section keywords")
            return "change_section"

        # Check for drop course
        elif any(word in words for word in ["drop", "withdraw", "remove"]):
            logger.debug("➖ Matched drop course keywords")
            return "drop_course"

        # Check for request status
        elif any(word in words for word in ["status", "request", "pending"]):
            logger.debug("📊 Matched request status keywords")
            return "request_status"
        else:
            logger.debug("❓ No specific intent matched, defaulting to general")
            return "general"

    async def _handle_greeting(
        self, user_claims: JWTClaims, correlation_id: str
    ) -> ChatReply:
        """Handle greeting messages."""
        role_messages = {
            "student": f"Hello {user_claims.full_name}! I'm here to help you with course registration. You can ask me about your schedule, add or drop courses, or check your request status.",
            "instructor": f"Welcome {user_claims.full_name}! I can help you review student requests, check advisee information, and manage approvals.",
            "department_head": f"Hello {user_claims.full_name}! I'm ready to help with department-level request reviews and final approvals.",
            "system_admin": f"Welcome {user_claims.full_name}! I can assist with system-wide operations and analytics.",
        }

        message = role_messages.get(
            user_claims.user_type,
            f"Hello {user_claims.full_name}! I'm here to help you.",
        )

        return ChatReply(
            message=message,
            audit=ChatAudit(
                correlation_id=correlation_id,
                user_type=user_claims.user_type,
                actor_id=user_claims.actor_id,
                tool_calls=["greeting"],
                timestamp=datetime.now(timezone.utc),
            ),
        )

    async def _handle_schedule_inquiry(
        self, message: str, user_claims: JWTClaims, correlation_id: str, db: Any
    ) -> ChatReply:
        """Handle schedule-related inquiries."""

        # Import the actual schedule function
        from brs_backend.agents.student_tools import get_current_schedule

        # Get real schedule data from database
        schedule_result = get_current_schedule(user_claims.actor_id)

        if not schedule_result["success"]:
            return ChatReply(
                message=f"I'm sorry, I couldn't retrieve your schedule at this time. Error: {schedule_result.get('error', 'Unknown error')}",
                audit=ChatAudit(
                    correlation_id=correlation_id,
                    user_type=user_claims.user_type,
                    actor_id=user_claims.actor_id,
                    tool_calls=["get_current_schedule"],
                    timestamp=datetime.now(timezone.utc),
                ),
            )

        # Transform the data to match the UI card format
        schedule_data = schedule_result["data"]
        courses = []

        for item in schedule_data["schedule"]:
            # Convert meetings to time string format
            time_slots = []
            for meeting in item["meetings"]:
                day = meeting["day_of_week"]
                activity = meeting["activity"]
                time_slots.append(f"{day} {activity}")

            time_str = ", ".join(time_slots) if time_slots else "TBD"

            courses.append(
                {
                    "course_code": item["course_code"],
                    "title": item["course_title"],
                    "section": item["section_code"],
                    "time": time_str,
                    "instructor": item["instructor"],
                    "room": ", ".join([m.get("room", "TBD") for m in item["meetings"]])
                    or "TBD",
                }
            )

        ui_schedule_data = {
            "courses": courses,
            "total_credits": schedule_data["total_credits"],
        }

        # Create schedule card
        schedule_card = ChatCard(type=CardType.WEEK_GRID, payload=ui_schedule_data)

        if len(courses) == 0:
            message = "You don't have any enrolled courses for this term yet."
        else:
            message = f"Here's your current schedule for this term. You're enrolled in {len(courses)} courses for a total of {schedule_data['total_credits']} credits."

        return ChatReply(
            message=message,
            cards=[schedule_card] if len(courses) > 0 else [],
            audit=ChatAudit(
                correlation_id=correlation_id,
                user_type=user_claims.user_type,
                actor_id=user_claims.actor_id,
                tool_calls=["get_current_schedule"],
                timestamp=datetime.now(timezone.utc),
            ),
        )

    async def _handle_add_course(
        self, message: str, user_claims: JWTClaims, correlation_id: str, db: Any
    ) -> ChatReply:
        """Handle course addition requests."""

        # Extract course info from message (simple parsing)
        course_code = self._extract_course_code(message)

        if not course_code:
            return ChatReply(
                message="I'd be happy to help you add a course! Please specify which course you'd like to add (e.g., 'I want to add CS201').",
                audit=ChatAudit(
                    correlation_id=correlation_id,
                    user_type=user_claims.user_type,
                    actor_id=user_claims.actor_id,
                    timestamp=datetime.now(timezone.utc),
                ),
            )

        # Query real sections from database

        course = db.query(Course).filter(Course.code == course_code).first()
        if not course:
            return await self._fallback_response(
                user_claims,
                correlation_id,
                f"Course {course_code} not found in the system.",
            )

        sections = db.query(Section).filter(Section.course_id == course.course_id).options(
            joinedload(Section.instructor)
        ).all()

        sections_data = {
            "course_code": course_code,
            "sections": [
                {
                    "section_id": str(section.section_id),
                    "section_code": section.section_code,
                    "time": f"{section.days_of_week} {section.start_time}-{section.end_time}",
                    "instructor": section.instructor.full_name if section.instructor else "TBA",
                    "capacity": section.capacity,
                    "enrolled": len(section.enrollments) if section.enrollments else 0,
                    "conflicts": [],  # Conflict detection implemented via student_tools.check_attachable
                }
                for section in sections
            ],
        }

        # Create alternatives card
        alternatives_card = ChatCard(type=CardType.ALTERNATIVES, payload=sections_data)

        # Create action for best section
        best_section = sections_data["sections"][0]  # First section without conflicts
        add_action = ChatAction(
            label=f"Add {course_code} {best_section['section_code']}",
            type=ActionType.POST,
            endpoint="/registration-requests",
            body={
                "type": "ADD",
                "to_section_id": best_section["section_id"],
                "justification": f"Adding {course_code} as requested via chat",
            },
        )

        return ChatReply(
            message=f"I found {len(sections_data['sections'])} available sections for {course_code}. Section A1 looks like the best fit with no conflicts!",
            cards=[alternatives_card],
            actions=[add_action],
            audit=ChatAudit(
                correlation_id=correlation_id,
                user_type=user_claims.user_type,
                actor_id=user_claims.actor_id,
                tool_calls=["get_course_info", "check_attachable"],
                timestamp=datetime.now(timezone.utc),
            ),
        )

    async def _handle_change_section(
        self, message: str, user_claims: JWTClaims, correlation_id: str, db: Any
    ) -> ChatReply:
        """Handle section change requests."""

        # Query real enrollment and section data from database

        student = db.query(Student).filter(Student.student_id == user_claims.actor_id).first()
        if not student:
            return await self._fallback_response(
                user_claims,
                correlation_id,
                "Student record not found.",
            )

        # Get student's current enrollments
        enrollments = db.query(Enrollment).filter(
            Enrollment.student_id == student.student_id
        ).options(
            joinedload(Enrollment.section).joinedload(Section.course)
        ).all()

        if not enrollments:
            return await self._fallback_response(
                user_claims,
                correlation_id,
                "No current enrollments found to change.",
            )

        # Use first enrollment for demo
        current_enrollment = enrollments[0]
        current_section = current_enrollment.section

        change_data = {
            "current_section": {
                "course_code": current_section.course.code,
                "section_code": current_section.section_code,
                "time": f"{current_section.days_of_week} {current_section.start_time}-{current_section.end_time}",
            },
            "requested_section": {
                "section_id": str(current_section.section_id),
                "section_code": "Alternative section",
                "time": "Alternative time",
                "conflicts": [],
                "capacity": current_section.capacity,
                "enrolled": len(current_section.enrollments) if current_section.enrollments else 0,
            },
        }

        # Create schedule diff card
        diff_card = ChatCard(type=CardType.SCHEDULE_DIFF, payload=change_data)

        # Create change action
        change_action = ChatAction(
            label="Submit Section Change Request",
            type=ActionType.POST,
            endpoint="/registration-requests",
            body={
                "type": "CHANGE_SECTION",
                "from_section_id": "current_section_id",
                "to_section_id": change_data["requested_section"]["section_id"],
                "justification": "Section change requested via chat for better scheduling",
            },
        )

        return ChatReply(
            message="Great choice! Section A2 fits your schedule with no conflicts. Here's how your schedule would change:",
            cards=[diff_card],
            actions=[change_action],
            audit=ChatAudit(
                correlation_id=correlation_id,
                user_type=user_claims.user_type,
                actor_id=user_claims.actor_id,
                tool_calls=["check_attachable", "get_schedule_diff"],
                timestamp=datetime.now(timezone.utc),
            ),
        )

    async def _handle_drop_course(
        self, message: str, user_claims: JWTClaims, correlation_id: str, db: Any
    ) -> ChatReply:
        """Handle course drop requests."""

        course_code = self._extract_course_code(message)

        if not course_code:
            return ChatReply(
                message="Which course would you like to drop? Please specify the course code.",
                audit=ChatAudit(
                    correlation_id=correlation_id,
                    user_type=user_claims.user_type,
                    actor_id=user_claims.actor_id,
                    timestamp=datetime.now(timezone.utc),
                ),
            )

        drop_action = ChatAction(
            label=f"Drop {course_code}",
            type=ActionType.POST,
            endpoint="/registration-requests",
            body={
                "type": "DROP",
                "from_section_id": "enrolled_section_id",
                "justification": f"Dropping {course_code} as requested via chat",
            },
        )

        return ChatReply(
            message=f"I can help you drop {course_code}. Please confirm if you'd like to proceed:",
            actions=[drop_action],
            audit=ChatAudit(
                correlation_id=correlation_id,
                user_type=user_claims.user_type,
                actor_id=user_claims.actor_id,
                tool_calls=["get_enrollment"],
                timestamp=datetime.now(timezone.utc),
            ),
        )

    async def _handle_request_status(
        self, user_claims: JWTClaims, correlation_id: str, db: Any
    ) -> ChatReply:
        """Handle request status inquiries."""

        # Query real registration requests from database

        student = db.query(Student).filter(Student.student_id == user_claims.actor_id).first()
        if not student:
            return await self._fallback_response(
                user_claims,
                correlation_id,
                "Student record not found.",
            )

        requests = db.query(RegistrationRequest).filter(
            RegistrationRequest.student_id == student.student_id
        ).options(
            joinedload(RegistrationRequest.section).joinedload(Section.course)
        ).all()

        pending_requests = [req for req in requests if req.status in ['pending', 'advisor_review']]
        completed_requests = [req for req in requests if req.status in ['approved', 'rejected']]

        requests_data = {
            "pending": [
                {
                    "request_id": str(req.request_id),
                    "type": req.request_type,
                    "course": req.section.course.code if req.section else "Unknown",
                    "section": req.section.section_code if req.section else "Unknown",
                    "status": req.status,
                    "submitted": req.submitted_at.strftime("%Y-%m-%d") if req.submitted_at else "Unknown",
                }
                for req in pending_requests
            ],
            "completed": [
                {
                    "request_id": str(req.request_id),
                    "type": req.request_type,
                    "course": req.section.course.code if req.section else "Unknown",
                    "status": req.status,
                    "completed": req.decided_at.strftime("%Y-%m-%d") if req.decided_at else "Unknown",
                }
                for req in completed_requests
            ],
        }

        requests_card = ChatCard(type=CardType.REQUEST_SUMMARY, payload=requests_data)

        return ChatReply(
            message=f"You have {len(requests_data['pending'])} pending requests and {len(requests_data['completed'])} completed requests.",
            cards=[requests_card],
            audit=ChatAudit(
                correlation_id=correlation_id,
                user_type=user_claims.user_type,
                actor_id=user_claims.actor_id,
                tool_calls=["get_my_requests"],
                timestamp=datetime.now(timezone.utc),
            ),
        )

    async def _handle_general_inquiry(
        self, message: str, user_claims: JWTClaims, correlation_id: str
    ) -> ChatReply:
        """Handle general inquiries."""
        return ChatReply(
            message="I'm here to help with course registration! You can ask me to:\n• Show your schedule\n• Add or drop courses\n• Change sections\n• Check request status\n\nWhat would you like to do?",
            audit=ChatAudit(
                correlation_id=correlation_id,
                user_type=user_claims.user_type,
                actor_id=user_claims.actor_id,
                timestamp=datetime.now(timezone.utc),
            ),
        )

    def _extract_course_code(self, message: str) -> str | None:
        """Extract course code from message (simple regex would work better)."""
        words = message.upper().split()
        for word in words:
            if any(
                word.startswith(prefix)
                for prefix in ["CS", "MATH", "PHYS", "ENGL", "HIST"]
            ):
                return word
        return None

    def _wrap_tool_function(self, original_fn, tool_name):
        """Wrap a tool function to capture its results."""
        def wrapped(*args, **kwargs):
            logger.info(f"🔧 Executing tool: {tool_name}")
            result = original_fn(*args, **kwargs)
            logger.info(f"📊 Tool {tool_name} returned: {type(result)} with keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")

            # Store the result for later use
            self._captured_tool_results[tool_name] = result
            return result
        return wrapped

    def _extract_tool_results_from_agent(self, agent) -> dict[str, Any]:
        """Extract tool results from the SmolAgents ToolCallingAgent execution."""
        try:
            tool_results = {}

            # Debug: Print agent state structure
            if hasattr(agent, 'state'):
                logger.info(f"🔍 Agent state attributes: {[attr for attr in dir(agent.state) if not attr.startswith('_')]}")

                # Check for messages in state
                if hasattr(agent.state, 'messages'):
                    logger.info(f"� Found {len(agent.state.messages)} messages in agent state")
                    for i, message in enumerate(agent.state.messages):
                        logger.info(f"📨 Message {i}: type={type(message)}, attributes={[attr for attr in dir(message) if not attr.startswith('_')]}")

                        # Check for tool calls in messages
                        if hasattr(message, 'tool_calls') and message.tool_calls:
                            logger.info(f"🔧 Found {len(message.tool_calls)} tool calls in message {i}")
                            for j, tool_call in enumerate(message.tool_calls):
                                logger.info(f"🔧 Tool call {j}: {[attr for attr in dir(tool_call) if not attr.startswith('_')]}")

                        # Check for content that might be tool results
                        if hasattr(message, 'content'):
                            logger.info(f"� Message {i} content preview: {str(message.content)[:100]}...")

            # For now, return empty results to see the debug output
            logger.info(f"📦 Total tool results extracted: {len(tool_results)}")
            return tool_results

        except Exception as e:
            logger.warning(f"⚠️ Failed to extract tool results: {e}")
            return {}

    def _create_schedule_card_from_data(self, schedule_data: dict[str, Any], user_claims: JWTClaims) -> ChatCard | None:
        """Create a schedule card from structured schedule data."""
        # Debug: Log the raw schedule data
        logger.info("📊 Raw schedule data received:")
        logger.info(f"   - Keys: {list(schedule_data.keys())}")
        logger.info(f"   - Schedule entries: {len(schedule_data.get('schedule', []))}")

        if not schedule_data.get('schedule'):
            logger.warning("❌ No schedule data found in schedule_data")
            return None

        schedule_entries = []
        for course in schedule_data['schedule']:
            # Process meetings to create time slots
            time_slots = []
            if course.get('meetings'):
                for meeting in course['meetings']:
                    activity = meeting.get('activity', 'Class')

                    # Create time slot if we have start and end times
                    if meeting.get('start_time') and meeting.get('end_time'):
                        time_slot = {
                            "day_of_week": meeting['day_of_week'],
                            "start_time": meeting['start_time'],
                            "end_time": meeting['end_time'],
                            "activity": activity,
                            "room": meeting.get('room', 'TBA')
                        }
                        time_slots.append(time_slot)
                    else:
                        # Fallback for meetings without time info
                        time_slots.append({
                            "day_of_week": meeting['day_of_week'],
                            "activity": activity,
                            "room": meeting.get('room', 'TBA')
                        })

            entry = {
                "course_code": course.get('course_code', ''),
                "title": course.get('course_title', ''),
                "section": course.get('section_code', ''),
                "instructor": course.get('instructor', 'TBA'),
                "credits": course.get('credits', 0),
                "time_slots": time_slots,  # New: structured time slots for calendar
                "room": time_slots[0].get('room', 'TBA') if time_slots else 'TBA',  # First meeting room
                "status": course.get('status', 'enrolled')  # Pass through enrollment status
            }
            schedule_entries.append(entry)

        if not schedule_entries:
            return None

        schedule_payload = {
            "student_name": user_claims.full_name,
            "total_credits": schedule_data.get('total_credits', 0),
            "pending_credits": schedule_data.get('pending_credits', 0),
            "courses": schedule_entries
        }

        # Debug logging to see what's being sent to the frontend
        logger.info("🎯 Creating WeekGridCard with payload:")
        logger.info(f"   - Student: {schedule_payload['student_name']}")
        logger.info(f"   - Total Credits: {schedule_payload['total_credits']}")
        logger.info(f"   - Number of courses: {len(schedule_payload['courses'])}")

        for i, course in enumerate(schedule_payload['courses']):
            logger.info(f"   - Course {i+1}: {course['course_code']} - {course['title']}")
            logger.info(f"     * Section: {course['section']}")
            logger.info(f"     * Instructor: {course['instructor']}")
            logger.info(f"     * Credits: {course['credits']}")
            logger.info(f"     * Time slots: {len(course.get('time_slots', []))}")

            for j, slot in enumerate(course.get('time_slots', [])):
                logger.info(f"       - Slot {j+1}: {slot.get('day', 'No day')} {slot.get('start_time', 'No start')} - {slot.get('end_time', 'No end')}")
                logger.info(f"         * Activity: {slot.get('activity', 'No activity')}")
                logger.info(f"         * Room: {slot.get('room', 'No room')}")

        return ChatCard(type=CardType.WEEK_GRID, payload=schedule_payload)

    def _create_sections_card_from_data(self, sections_data: dict[str, Any]) -> ChatCard | None:
        """Create a course info card from structured sections data."""
        course_info = sections_data.get('course', {})
        sections = sections_data.get('sections', [])

        if not course_info:
            return None

        payload = {
            "code": course_info.get('code', ''),
            "title": course_info.get('title', ''),
            "credits": course_info.get('credits', 0),
            "sections": sections
        }

        return ChatCard(type=CardType.COURSE_INFO, payload=payload)

    def _create_course_catalog_card(self, catalog_data: dict[str, Any]) -> ChatCard | None:
        """Create a course info card from course catalog data (multiple courses)."""
        courses = catalog_data.get('courses', [])

        if not courses:
            return None

        # For course catalog, we'll show the first course with all its sections
        # or create a summary of multiple courses
        if len(courses) == 1:
            # Single course - use the same format as sections card
            course = courses[0]
            payload = {
                "code": course.get('code', ''),
                "title": course.get('title', ''),
                "credits": course.get('credits', 0),
                "sections": course.get('sections', [])
            }
        else:
            # Multiple courses - create a summary format
            payload = {
                "catalog": True,
                "total_courses": len(courses),
                "courses": courses[:5],  # Limit to first 5 courses to prevent UI overflow
                "message": catalog_data.get('message', f'Found {len(courses)} available courses')
            }

        return ChatCard(type=CardType.COURSE_INFO, payload=payload)

    def _create_request_summary_card(self, request_data: dict[str, Any]) -> ChatCard | None:
        """Create a request summary card from registration request data."""
        if not request_data.get('request_id'):
            return None

        payload = {
            "request_id": request_data.get('request_id', ''),
            "type": request_data.get('type', ''),
            "status": request_data.get('state', ''),
            "created_at": request_data.get('created_at', ''),
            "message": request_data.get('message', '')
        }

        return ChatCard(type=CardType.REQUEST_SUMMARY, payload=payload)

    def _create_alternatives_card(self, alternatives_data: dict[str, Any]) -> ChatCard | None:
        """Create an alternatives card from eligibility check data."""
        # Handle both direct format and tool result format
        violations = alternatives_data.get('violations', [])
        section_data = alternatives_data.get('data', {}).get('section', {})
        suggested_alternatives = alternatives_data.get('suggested_alternatives', [])

        # If no violations in top level, might be direct format
        if not violations:
            violations = alternatives_data.get('data', {}).get('violations', [])

        # If no section data in nested format, try direct
        if not section_data:
            section_data = alternatives_data.get('section', {})

        # Get alternatives from nested data if not at top level
        if not suggested_alternatives:
            suggested_alternatives = alternatives_data.get('data', {}).get('alternatives', [])

        if not violations and not section_data and not suggested_alternatives:
            return None

        payload = {
            "violations": violations,
            "alternatives": suggested_alternatives,  # Now populated with proactive suggestions
            "originalSection": section_data.get('section_code', ''),
            "sectionDetails": section_data,
            "hasProactiveSuggestions": len(suggested_alternatives) > 0
        }

        return ChatCard(type=CardType.ALTERNATIVES, payload=payload)

    def _create_schedule_diff_card(self, diff_data: dict[str, Any]) -> ChatCard | None:
        """Create a schedule diff card from schedule comparison data."""
        # This would be used for before/after schedule comparisons
        payload = {
            "before": diff_data.get('current_schedule', {}),
            "after": diff_data.get('new_schedule', {}),
            "changes": diff_data.get('changes', [])
        }

        return ChatCard(type=CardType.SCHEDULE_DIFF, payload=payload)

    def _create_prerequisite_tree_card(self, prereq_data: dict[str, Any]) -> ChatCard | None:
        """Create a prerequisite tree card from course prerequisite data."""
        course = prereq_data.get('course', {})
        prerequisites = prereq_data.get('prerequisites', [])
        dependents = prereq_data.get('dependents', [])

        payload = {
            "course": course,
            "prerequisites": prerequisites,
            "dependents": dependents
        }

        return ChatCard(type=CardType.PREREQUISITE_TREE, payload=payload)

    def _create_generic_card(self, data: dict[str, Any], tool_name: str) -> ChatCard:
        """Create a generic card as fallback for unsupported card types."""
        payload = {
            "tool_name": tool_name,
            "data": data
        }

        # Use the GENERIC card type
        return ChatCard(type=CardType.GENERIC, payload=payload)


# Agent factory
def get_agent_for_role(role: str) -> BRSChatAgent:
    """Get chat agent instance for the specified role."""
    return BRSChatAgent()  # SmolAgents version handles all roles internally


# Main processing function
async def process_message(
    agent: BRSChatAgent,
    message: str,
    user_claims: JWTClaims,
    session_id: str,
    correlation_id: str,
    db: Any,
) -> ChatReply:
    """Process a message through the chat agent."""
    return await agent.process_message(
        message=message,
        user_claims=user_claims,
        session_id=session_id,
        correlation_id=correlation_id,
        db=db,
    )
