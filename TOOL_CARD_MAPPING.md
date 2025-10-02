# Tool Response to Card Mapping Architecture - Priority-Ordered System

## Overview

The BRS system uses a **priority-ordered card type architecture** where:
1. **Student tools** return structured JSON responses with `{success, preferred_card_types, data, error}` format
2. **Chat agent** processes these responses and selects the best available card type from the priority list
3. **Frontend** renders cards using the `CardRenderer` component with automatic fallback support

## Priority-Ordered Card Selection

### Tool Response Format:
```json
{
  "success": boolean,
  "preferred_card_types": ["primary_type", "fallback_type", "generic"],
  "data": {...},      // Tool-specific structured data
  "error": string     // Error message if success=false
}
```

### Selection Algorithm:
1. **Tool specifies priority list**: Each tool returns `preferred_card_types` as an ordered array
2. **Frontend compatibility check**: System checks which card types are supported by frontend
3. **Best match selection**: First supported card type from the priority list is selected
4. **Generic fallback**: If no preferred types are supported, defaults to `generic` card

## Supported Card Types

### Frontend Card Components:
- ✅ `week_grid` - Interactive weekly schedule with time slots
- ✅ `schedule_diff` - Before/after schedule comparisons
- ✅ `request_summary` - Registration request status and details
- ✅ `alternatives` - Alternative section recommendations
- ✅ `course_info` - Course information with available sections
- ✅ `prerequisite_tree` - Hierarchical prerequisite visualization
- ✅ `generic` - **Universal fallback** - JSON data display

### Backend Card Types (`CardType` enum):
```python
class CardType(str, Enum):
    WEEK_GRID = "week_grid"
    SCHEDULE_DIFF = "schedule_diff"
    REQUEST_SUMMARY = "request_summary"
    ALTERNATIVES = "alternatives"
    COURSE_INFO = "course_info"
    PREREQUISITE_TREE = "prerequisite_tree"
    GENERIC = "generic"  # Universal fallback
```

## Tool → Card Priority Mappings

### 1. `get_current_schedule()`
**Priority:** `["week_grid", "schedule_diff", "generic"]`
- **Primary:** `week_grid` - Rich schedule visualization
- **Fallback:** `schedule_diff` - If current schedule comparison needed
- **Final:** `generic` - Raw JSON display

**Tool Response:**
```json
{
  "success": true,
  "preferred_card_types": ["week_grid", "schedule_diff", "generic"],
  "data": {
    "schedule": [...],
    "total_credits": 12,
    "course_count": 4
  }
}
```

### 2. `search_sections()`
**Priority:** `["course_info", "alternatives", "generic"]`
- **Primary:** `course_info` - Course details with sections
- **Fallback:** `alternatives` - If showing alternative options
- **Final:** `generic` - Raw JSON display

### 3. `create_registration_request()`
**Priority:** `["request_summary", "generic"]`
- **Primary:** `request_summary` - Request status and details
- **Final:** `generic` - Raw JSON display

### 4. `check_attachable()`
**Priority:** `["alternatives", "course_info", "generic"]` (if violations) OR `["course_info", "generic"]` (if successful)
- **Dynamic Priority:** Changes based on eligibility result
- **With Violations:** Shows alternatives first, then course info
- **Without Violations:** Shows course info directly

### 5. `get_student_info()`
**Priority:** `["course_info", "generic"]`
- **Primary:** `course_info` - Student academic information
- **Final:** `generic` - Raw JSON display

### 6. `check_pending_requests()`
**Priority:** `["request_summary", "generic"]`
- **Primary:** `request_summary` - Pending request status
- **Final:** `generic` - Raw JSON display

## Card Selection Examples

### Example 1: Successful Week Grid
```python
# Tool response
{
  "success": true,
  "preferred_card_types": ["week_grid", "schedule_diff", "generic"],
  "data": {...}
}

# Selection process:
# 1. Check "week_grid" → ✅ Supported → Selected!
# 2. Create WeekGridCard with payload
```

### Example 2: Unsupported Primary Type
```python
# Tool response (hypothetical)
{
  "success": true,
  "preferred_card_types": ["gantt_chart", "week_grid", "generic"],
  "data": {...}
}

# Selection process:
# 1. Check "gantt_chart" → ❌ Not supported by frontend
# 2. Check "week_grid" → ✅ Supported → Selected!
# 3. Create WeekGridCard with payload
```

### Example 3: Generic Fallback
```python
# Tool response (hypothetical)
{
  "success": true,
  "preferred_card_types": ["custom_viz", "pie_chart"],
  "data": {...}
}

# Selection process:
# 1. Check "custom_viz" → ❌ Not supported
# 2. Check "pie_chart" → ❌ Not supported
# 3. Default to "generic" → ✅ Always supported
# 4. Create GenericCard with raw JSON
```

## Dynamic Priority Logic

### Conditional Card Selection:
Some tools use conditional logic to set priorities based on data:

```python
# check_attachable tool example
violations = check_registration_violations(...)

if violations:
    preferred_types = ["alternatives", "course_info", "generic"]
else:
    preferred_types = ["course_info", "generic"]

return {
    "success": True,
    "preferred_card_types": preferred_types,
    "data": {...}
}
```

## Frontend Fallback Rendering

The `CardRenderer` component handles unknown card types gracefully:

```jsx
function CardComponent({ card }) {
    switch (card.type) {
        case 'week_grid':
            return <WeekGridCard {...card.payload} />;
        case 'course_info':
            return <CourseInfoCard {...card.payload} />;
        // ... other supported types
        default:
            return <GenericCard card={card} />; // Automatic fallback
    }
}
```

## Benefits of Priority-Ordered System

### 1. **Graceful Degradation**
- Tools continue working even if preferred card types aren't supported
- Generic card provides complete data visibility
- No broken UI experiences

### 2. **Forward Compatibility**
- New card types can be added without breaking existing tools
- Tools can specify new preferred types while maintaining fallbacks
- Frontend can be enhanced incrementally

### 3. **Context-Aware Rendering**
- Tools choose optimal visualization based on data content
- Dynamic priorities adapt to different scenarios
- Intelligent fallbacks for edge cases

### 4. **Development Flexibility**
- Frontend developers can implement card types at their own pace
- Backend tools specify intent without tight coupling
- Easy testing with generic fallback

## Implementation Status

### ✅ Completed:
- Priority-ordered card type system implemented
- All student tools updated with preferred_card_types
- Chat agent selection algorithm implemented
- Generic fallback card type added
- Dynamic priority logic for conditional cases

### 🔧 Usage Examples:

#### Adding New Card Types:
```python
# 1. Add to CardType enum
class CardType(str, Enum):
    # ... existing types
    NEW_VISUALIZATION = "new_visualization"

# 2. Update tool priorities
return {
    "preferred_card_types": ["new_visualization", "week_grid", "generic"],
    # ...
}

# 3. Implement frontend component (optional - generic handles fallback)
```

#### Testing Card Fallbacks:
```python
# Tool can specify experimental types
return {
    "preferred_card_types": ["experimental_3d_viz", "week_grid", "generic"],
    # ...
}
# → Will use week_grid until experimental_3d_viz is implemented
```

## Next Enhancement Opportunities

1. **Advanced Priority Logic**: Implement user preference-based card selection
2. **A/B Testing Support**: Tools can specify multiple primary options for testing
3. **Performance Optimization**: Cache card type compatibility checks
4. **Analytics Integration**: Track which card types are most effective
5. **Dynamic Card Composition**: Combine multiple card types in single response
