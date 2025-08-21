# PRD: LocAIted Single-Flow React UI (Lean Version)

## Product Overview
A streamlined React web application that enables photojournalists to discover newsworthy events through a single, unified flow combining profile information and query parameters.

## Objectives
- **Primary:** Enable event discovery in one seamless interaction
- **Constraint:** Deploy within 8 hours with lean, focused implementation

## User Flow

### Single Flow: Discover Events
1. User fills combined form with profile and query details
2. User clicks "Discover Events"
3. System shows real-time agent processing status
4. Results appear in card view
5. User can export results or start new search

## Functional Requirements

### 1. Input Form Section
**Profile Fields:**
- **Location** (Required)
  - Dropdown: NYC, DC, LA, Chicago, Boston, Custom
  - Custom reveals text input field
  - Default: NYC
- **Credentials** (Required)
  - Radio buttons: Press Pass, Public Only, VIP Access
  - Default: Public Only
- **Interest Areas** (Required)
  - Multi-select chips: Protests, Cultural, Political, Fashion, Sports, Tech, Arts
  - Minimum: 1, Maximum: 5
- **Previous Events** (Optional)
  - File upload: Accept .csv
  - Skip button if not available

**Query Fields:**
- **Time Window** (Required)
  - Dropdown: Next 7 days, Next 14 days, Next 30 days
  - Default: Next 7 days
- **Looking For** (Required)
  - Text input, 10-200 characters
  - Placeholder: "e.g., climate protests, art gallery openings"

**Actions:**
- "Discover Events" button (primary action)
- "Clear Form" button (secondary action)

### 2. Status Section
**During Processing:**
- Step indicator with agent-specific messaging:
  1. "Editor is building your profile..."
  2. "Researcher is surfacing potential events..."
  3. "Fact-Checker is gathering event details..."
  4. "Publisher is evaluating if events are worth your time..."
- Simple progress bar

**After Completion:**
- Collapsible metrics panel (collapsed by default):
  - Toggle button: "Show Metrics"
  - When expanded: Total cost, Cache hits, Processing time
- Main display: "{X} events found"

### 3. Results Section

**Card View Only (Calendar is bonus for later):**
Each event card displays:
- **Title** (bold, prominent)
- **Date & TIME** (TIME in emphasized format)
- **Location** (with map link if available)
- **Access Requirements** (badge style: Public/Press/VIP)
- **Description** (2-3 lines)
- **Why Recommended** (italic, smaller text)
- **Photo Score** (visual indicator, 0-100)

**Controls:**
- Sort dropdown: Date (default), Score
- Export button: Download CSV

## Non-Functional Requirements

### Performance
- API response handling: Show status immediately
- Total workflow time: ~30-60 seconds expected

### Design
- Clean, functional interface
- Desktop-only (no mobile responsiveness needed)
- Focus on readability and quick scanning

### Browser Support
- Chrome 90+ (primary)
- Firefox/Safari/Edge (nice to have)

### Code Quality & Testing Requirements
- **Code Standards:**
  - Consistent naming conventions (camelCase for variables, PascalCase for components)
  - Prop validation using PropTypes
  - Meaningful component and variable names
  - Comments for complex logic only
  - No console.logs in production code

- **Testing Approach:**
  - Manual testing of complete user flow
  - Test form validation edge cases
  - Test API error scenarios
  - Test export functionality
  - Browser console must be error-free

- **Code Organization:**
  - Separate API calls into services folder
  - Reusable components in components folder
  - Constants in separate config file
  - Clean separation of concerns

## Technical Specifications

### Frontend Stack
- **Framework:** React 18
- **Build Tool:** Vite
- **UI Library:** Material-UI v5
- **HTTP Client:** Axios
- **State:** React hooks (useState only)
- **Prop Validation:** PropTypes

### API Integration
**Extended SearchRequest:**
```json
{
  "location": "NYC",
  "custom_location": "Washington DC",
  "credentials": "press_pass",
  "interest_areas": ["protests", "cultural"],
  "csv_file": "base64_encoded_file",
  "days_ahead": 14,
  "query": "climate protests and art exhibitions"
}
```

### Component Structure (Simplified)
```
src/
├── App.jsx
├── components/
│   ├── EventDiscoveryForm.jsx
│   ├── StatusIndicator.jsx
│   ├── ResultsContainer.jsx
│   ├── MetricsPanel.jsx
│   ├── EventCard.jsx
│   └── ExportButton.jsx
├── services/
│   └── api.js
├── utils/
│   └── csvExport.js
└── config/
    └── constants.js
```

## Success Metrics (Frontend-Focused)
- **Critical:** Form submission works without errors
- **Critical:** Status updates display during processing
- **Critical:** Events render correctly when received
- **Important:** Export to CSV functions properly
- **Important:** All form validations work
- **Important:** Clean code with no console errors

## Implementation Timeline (6 hours + 2 hour buffer)

**Hour 1:** Setup & Core Structure
- Initialize React with Vite
- Install MUI and Axios
- Basic component structure

**Hour 2-3:** Input Form
- Build form with all fields
- Add validation
- Handle custom location toggle
- CSV upload (basic)

**Hour 4:** API Integration
- Extend backend SearchRequest
- Connect form to API
- Handle responses

**Hour 5:** Results Display
- Event card component
- Render event list
- Sorting functionality

**Hour 6:** Polish & Export
- Status indicators with agent messaging
- Collapsible metrics panel
- CSV export
- Error handling

**Hours 7-8:** Testing & Deployment
- Complete flow testing
- Fix any bugs
- Deploy to production

## BONUS Features (Only if time permits)
- Calendar view
- Filter by access type
- Better loading animations
- Event score visualization

## Out of Scope (Lean MVP)
- Mobile responsiveness
- Add to calendar functionality
- User authentication
- Profile persistence
- Search history
- Feedback collection
- Multi-language support
- Advanced filtering
- Pagination

## Risks & Mitigations
- **Risk:** API integration delays
  - **Mitigation:** Test with mock data first
- **Risk:** CSV parsing complexity
  - **Mitigation:** Basic parsing only, make optional
- **Risk:** Time overrun
  - **Mitigation:** Core flow first, skip bonus features

## Definition of Done
- [ ] Form accepts all inputs and validates
- [ ] API call succeeds with extended request
- [ ] Agent status messages display during processing
- [ ] Events display in card format
- [ ] Export to CSV works
- [ ] Metrics panel toggles correctly
- [ ] No console errors
- [ ] Code follows established standards
- [ ] Manual testing completed
- [ ] Deployed and accessible

## Key Differences from Original PRD
1. Added DC and custom location options
2. Removed custom date range (fixed options only)
3. Agent-specific status messaging
4. Collapsible metrics (not always visible)
5. Calendar view moved to bonus
6. Removed "Add to Calendar" action
7. Frontend-only success metrics
8. No mobile responsiveness requirement
9. Reduced timeline focus on core features
10. Added code quality and testing requirements