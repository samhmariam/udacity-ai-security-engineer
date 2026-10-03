# Product Requirements Document

## Real-Time Collaboration Feature

------------------------------------------------------------------------

**Document ID:** PRD-2023-015 **Version:** 1.2 **Author:** Michael Brown, Product Manager **Last Updated:** June 20, 2023 **Status:** Approved for Development

------------------------------------------------------------------------

## 1. Overview

### 1.1 Summary

This PRD outlines the requirements for adding real-time collaboration capabilities to the Northstar dashboard builder. This feature will allow multiple users to simultaneously view and edit dashboards, with live presence indicators and conflict resolution.

### 1.2 Background

Customer feedback and competitive analysis have identified real-time collaboration as a top-requested feature. Currently, users must coordinate offline to avoid overwriting each other’s changes, leading to frustration and reduced adoption of the dashboard builder.

### 1.3 Goals

| Goal                              | Metric                     | Target    |
|-----------------------------------|----------------------------|-----------|
| Increase dashboard collaboration  | Users per dashboard (avg)  | 3.5 → 5.0 |
| Reduce support tickets            | Edit conflict tickets      | -80%      |
| Improve NPS for dashboard feature | Feature NPS                | 45 → 60   |
| Drive Enterprise upgrades         | Enterprise conversion rate | +15%      |

### 1.4 Non-Goals

- Real-time data refresh (separate initiative)
- Co-editing of other artifacts (reports, data sources)
- Video/audio communication features
- Mobile app support (Phase 2)

------------------------------------------------------------------------

## 2. User Stories

### 2.1 Primary User Stories

**US-1: View Collaborators** \> As a dashboard viewer, I want to see who else is viewing the same dashboard so that I know if my colleagues are working on it.

Acceptance Criteria: - Display avatar/initials for each active viewer - Show list of viewers on hover - Update presence within 5 seconds of user joining/leaving

**US-2: Collaborative Editing** \> As a dashboard editor, I want to edit a dashboard simultaneously with my colleagues so that we can build dashboards together efficiently.

Acceptance Criteria: - Multiple users can add/edit/remove widgets concurrently - Changes appear for all users within 1 second - No data loss when multiple users edit simultaneously

**US-3: Cursor Tracking** \> As a dashboard editor, I want to see where my colleagues are clicking/working so that I can avoid editing the same area.

Acceptance Criteria: - Display labeled cursors for each active editor - Cursors move smoothly with \< 200ms latency - Cursors disappear when user becomes inactive

**US-4: Conflict Resolution** \> As a dashboard editor, I want the system to handle conflicting edits gracefully so that no work is lost.

Acceptance Criteria: - Last-write-wins for simple property changes - Merge strategy for additive changes (adding widgets) - User notification when their change was superseded - Ability to undo/redo affected changes

**US-5: Edit Locking (Optional)** \> As a dashboard editor, I want to lock a widget while editing so that others cannot make conflicting changes.

Acceptance Criteria: - Visual indicator when widget is locked by another user - Lock automatically releases after 30 seconds of inactivity - Manual lock release option for lock holder

------------------------------------------------------------------------

## 3. Functional Requirements

### 3.1 Presence System

| ID     | Requirement                                               | Priority |
|--------|-----------------------------------------------------------|----------|
| FR-1.1 | Display presence indicator showing count of active users  | P0       |
| FR-1.2 | Show user avatars/initials for up to 5 users, +N for more | P0       |
| FR-1.3 | Display user names and roles on hover                     | P1       |
| FR-1.4 | Update presence within 5 seconds of state change          | P0       |
| FR-1.5 | Handle network disconnection gracefully (show as “away”)  | P1       |

### 3.2 Real-Time Sync

| ID     | Requirement                                           | Priority |
|--------|-------------------------------------------------------|----------|
| FR-2.1 | Sync widget additions across all connected clients    | P0       |
| FR-2.2 | Sync widget deletions across all connected clients    | P0       |
| FR-2.3 | Sync widget property changes (position, size, config) | P0       |
| FR-2.4 | Sync changes within 1 second under normal conditions  | P0       |
| FR-2.5 | Queue changes during temporary disconnection          | P1       |
| FR-2.6 | Reconcile queued changes on reconnection              | P1       |

### 3.3 Cursor Tracking

| ID     | Requirement                                   | Priority |
|--------|-----------------------------------------------|----------|
| FR-3.1 | Display colored cursor for each active editor | P1       |
| FR-3.2 | Label cursor with user name                   | P1       |
| FR-3.3 | Update cursor position with \< 200ms latency  | P1       |
| FR-3.4 | Hide cursor after 10 seconds of inactivity    | P2       |
| FR-3.5 | Throttle cursor updates to reduce bandwidth   | P2       |

### 3.4 Conflict Resolution

| ID     | Requirement                                              | Priority |
|--------|----------------------------------------------------------|----------|
| FR-4.1 | Implement operational transformation or CRDT for merging | P0       |
| FR-4.2 | Display toast notification when edit is superseded       | P1       |
| FR-4.3 | Maintain edit history for undo/redo                      | P0       |
| FR-4.4 | Allow undo of remote changes to own edits                | P2       |

### 3.5 Permissions

| ID     | Requirement                                          | Priority |
|--------|------------------------------------------------------|----------|
| FR-5.1 | Respect existing view/edit permissions               | P0       |
| FR-5.2 | Viewers see presence and cursor tracking (read-only) | P0       |
| FR-5.3 | Only editors can make changes                        | P0       |
| FR-5.4 | Admin can force-disconnect users if needed           | P2       |

------------------------------------------------------------------------

## 4. Non-Functional Requirements

### 4.1 Performance

| ID      | Requirement                    | Target       |
|---------|--------------------------------|--------------|
| NFR-1.1 | Sync latency (P95)             | \< 1 second  |
| NFR-1.2 | Cursor latency (P95)           | \< 200ms     |
| NFR-1.3 | Presence update latency        | \< 5 seconds |
| NFR-1.4 | Concurrent users per dashboard | Up to 25     |
| NFR-1.5 | Memory overhead per connection | \< 5MB       |

### 4.2 Reliability

| ID      | Requirement                           | Target     |
|---------|---------------------------------------|------------|
| NFR-2.1 | Sync success rate                     | \> 99.9%   |
| NFR-2.2 | Zero data loss from conflicts         | 100%       |
| NFR-2.3 | Graceful degradation on server issues | Required   |
| NFR-2.4 | Auto-reconnect on connection loss     | Within 30s |

### 4.3 Scalability

| ID      | Requirement                                    | Target   |
|---------|------------------------------------------------|----------|
| NFR-3.1 | Support 1000 concurrent collaboration sessions | Required |
| NFR-3.2 | Horizontal scaling of sync infrastructure      | Required |

### 4.4 Security

| ID      | Requirement                         | Target   |
|---------|-------------------------------------|----------|
| NFR-4.1 | WebSocket connections authenticated | Required |
| NFR-4.2 | All sync traffic encrypted (WSS)    | Required |
| NFR-4.3 | Permission check on every operation | Required |

------------------------------------------------------------------------

## 5. Technical Approach

### 5.1 Architecture

    ┌─────────────────────────────────────────────────────────────┐
    │                       Client (Browser)                       │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
    │  │  Dashboard  │  │  Presence   │  │  Collaboration      │  │
    │  │  Editor     │  │  Manager    │  │  Engine (Y.js/CRDT) │  │
    │  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
    │         └────────────────┼─────────────────────┘            │
    │                          │ WebSocket                        │
    └──────────────────────────┼──────────────────────────────────┘
                               │
    ┌──────────────────────────┼──────────────────────────────────┐
    │                    Sync Server (New)                        │
    │  ┌─────────────┐  ┌─────────────┐  ┌───────────────────┐   │
    │  │  WebSocket  │  │  Room       │  │  Persistence      │   │
    │  │  Gateway    │  │  Manager    │  │  Layer            │   │
    │  └─────────────┘  └─────────────┘  └─────────┬─────────┘   │
    │                                              │              │
    └──────────────────────────────────────────────┼──────────────┘
                                                   │
                                   ┌───────────────┼───────────────┐
                                   │               │               │
                            ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
                            │    Redis    │ │     RDS     │ │     S3      │
                            │  (Presence) │ │  (State)    │ │  (History)  │
                            └─────────────┘ └─────────────┘ └─────────────┘

### 5.2 Technology Choices

| Component        | Technology       | Rationale                            |
|------------------|------------------|--------------------------------------|
| CRDT Library     | Y.js             | Proven, performant, well-documented  |
| WebSocket Server | Node.js + ws     | Team familiarity, async performance  |
| Presence Store   | Redis            | Low latency, pub/sub support         |
| Sync State       | PostgreSQL (RDS) | Consistency, existing infrastructure |

### 5.3 Data Model Changes

New tables required:

    -- Collaboration session metadata
    CREATE TABLE collaboration_sessions (
        id UUID PRIMARY KEY,
        dashboard_id UUID REFERENCES dashboards(id),
        created_at TIMESTAMP,
        updated_at TIMESTAMP,
        state_vector BYTEA  -- Y.js state
    );

    -- Active presence tracking (Redis primary, DB backup)
    CREATE TABLE collaboration_presence (
        session_id UUID REFERENCES collaboration_sessions(id),
        user_id UUID REFERENCES users(id),
        joined_at TIMESTAMP,
        last_seen_at TIMESTAMP,
        cursor_state JSONB,
        PRIMARY KEY (session_id, user_id)
    );

------------------------------------------------------------------------

## 6. User Interface

### 6.1 Presence Indicator

Located in the dashboard header, next to the title: - Avatar stack showing up to 5 users - “+N more” indicator if \> 5 users - Green dot indicates active, yellow indicates idle - Hover to see full list with names

### 6.2 Cursor Display

- Colored arrow cursor with name label
- Color assigned per user (consistent within session)
- Fades out after 10 seconds of inactivity
- Toggle option in user preferences to hide others’ cursors

### 6.3 Conflict Notification

Toast notification (bottom-right): - “Your change was updated by \[User Name\]” - “Undo” action button - Auto-dismiss after 5 seconds

### 6.4 Wireframes

*\[Wireframes to be attached by Design team\]*

------------------------------------------------------------------------

## 7. Release Plan

### 7.1 Phased Rollout

| Phase  | Audience                 | Duration | Success Criteria |
|--------|--------------------------|----------|------------------|
| Alpha  | Internal team            | 2 weeks  | No P0/P1 bugs    |
| Beta   | 10 Enterprise customers  | 3 weeks  | NPS \> 50        |
| GA     | All Enterprise customers | \-       | Feature complete |
| Growth | Professional tier        | Q4 2023  | \-               |

### 7.2 Feature Flags

- `collaboration.enabled` - Master toggle
- `collaboration.cursors` - Cursor tracking
- `collaboration.locks` - Widget locking (experimental)

### 7.3 Rollback Plan

If critical issues discovered: 1. Disable feature flag globally 2. Users fall back to existing single-user editing 3. No data loss (changes saved normally)

------------------------------------------------------------------------

## 8. Success Metrics

### 8.1 Key Metrics

| Metric                          | Current  | Target            | Measurement   |
|---------------------------------|----------|-------------------|---------------|
| Avg users per dashboard session | 1.2      | 2.5               | Analytics     |
| Collaboration feature adoption  | N/A      | 40% of dashboards | Analytics     |
| Edit conflict support tickets   | 45/month | \< 10/month       | Zendesk       |
| Dashboard feature NPS           | 45       | 60                | In-app survey |

### 8.2 Monitoring

- Real-time dashboard for sync latency and errors
- Alerts for \> 2s sync latency (P95)
- Weekly metrics review during beta

------------------------------------------------------------------------

## 9. Open Questions

| ID  | Question                            | Owner       | Status           |
|-----|-------------------------------------|-------------|------------------|
| Q1  | Should we limit concurrent editors? | Product     | Decided: 25 max  |
| Q2  | Offline editing support needed?     | Engineering | Defer to Phase 2 |
| Q3  | Integration with comments feature?  | Design      | Under discussion |

------------------------------------------------------------------------

## 10. Appendix

### A. Competitive Analysis

| Competitor   | Real-time Collab | Presence | Cursors |
|--------------|------------------|----------|---------|
| Competitor A | Yes              | Yes      | Yes     |
| Competitor B | No               | Yes      | No      |
| Competitor C | Yes              | Yes      | No      |

### B. Customer Feedback

> “We have a team of 5 analysts who need to work on dashboards together. Right now we have to take turns or risk losing work.” - Velocity Financial Group
>
> “Real-time collaboration is table stakes for us. It’s why we’re evaluating alternatives.” - Atlas Manufacturing Co

### C. References

- Y.js Documentation: https://docs.yjs.dev/
- Figma Engineering Blog: Real-time Collaboration

------------------------------------------------------------------------

**Document Approval**

| Role             | Name              | Date          |
|------------------|-------------------|---------------|
| Product Manager  | Michael Brown     | June 20, 2023 |
| Engineering Lead | Sarah Chen        | June 21, 2023 |
| Design Lead      | Emily Davis       | June 21, 2023 |
| VP Product       | Jennifer Williams | June 22, 2023 |
