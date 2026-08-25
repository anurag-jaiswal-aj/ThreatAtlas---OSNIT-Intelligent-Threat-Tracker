# ThreatAtlas — Outstanding GitHub Issues & Backlog

This document provides a detailed breakdown of 6 identified bugs, performance issues, and feature enhancements for the ThreatAtlas OSINT Threat Intelligence Platform.

Each issue is formatted using standard GitHub Issue markdown specifications, including root cause analyses, precise code references, action items, and verifiable acceptance criteria.

---

## Summary of Issues

| ID | Title | Type | Priority | Affected Components |
|---|---|---|---|---|
| [#1](#issue-1-perf-frontend-ui-and-3d-globe-lag--performance-degradation) | `[PERF] Frontend UI and 3D Globe Lag / Performance Degradation` | Performance | **High** | `frontend/src/components/GlobeViewer.tsx`, `App.tsx` |
| [#2](#issue-2-bug-metric-counts-dynamically-fluctuate-when-switching-filter-tabs) | `[BUG] Metric Counts Dynamically Fluctuate When Switching Filter Tabs` | Bug | **Medium** | `FilterPanel.tsx`, `App.tsx`, `events.py` |
| [#3](#issue-3-nlpdata-irrelevant-general-news-ingested-as-security-threats-threat-relevance-filtering) | `[NLP/DATA] Irrelevant General News Ingested as Security Threats` | Bug / Data Quality | **High** | `rss_collector.py`, `preprocessing.py`, `threat_scorer.py` |
| [#4](#issue-4-feat-expand-osint-ingestion-to-multi-source-public-feeds) | `[FEAT] Expand OSINT Ingestion to Multi-Source Public Feeds` | Feature | **Medium** | `ingestion/config.py`, `rss_collector.py`, `intelligence/config.py` |
| [#5](#issue-5-bug-inconsistent-3d-globe-point-clickability-and-hit-testing) | `[BUG] Inconsistent 3D Globe Point Clickability and Hit-Testing` | Bug / UX | **Medium** | `frontend/src/components/GlobeViewer.tsx` |
| [#6](#issue-6-enhancement-configurable-threat-score-threshold-filter-for-3d-globe-display) | `[ENHANCEMENT] Configurable Threat Score Threshold Filter` | Enhancement | **Medium** | `FilterPanel.tsx`, `GlobeViewer.tsx`, `client.ts`, `events.py` |

---

## Issue 1: [PERF] Frontend UI and 3D Globe Lag / Performance Degradation

### Metadata
- **Title**: `[PERF] Frontend UI and 3D Globe Lag / Performance Degradation`
- **Labels**: `performance`, `frontend`, `cesium`, `ui/ux`
- **Priority**: **High**
- **Affected Area**: `frontend/src/components/GlobeViewer.tsx`, `frontend/src/App.tsx`

### Problem Description & Current Behavior
When displaying tens or hundreds of threat events on the 3D Cesium globe, the browser experiences noticeable frame drops, high CPU/GPU rendering load, and interface stuttering during pan/zoom or real-time WebSocket updates.

### Expected Behavior
The 3D globe should maintain a smooth 60 FPS rendering rate during camera flyTo animations and user interaction. State updates from real-time WebSockets should update markers without triggering full React component tree re-renders or recreating all Cesium entities from scratch.

### Root Cause Analysis
1. **Entity Collection Destruction & Recreation**:
   In `frontend/src/components/GlobeViewer.tsx`:
   ```typescript
   useEffect(() => {
     const viewer = viewerRef.current;
     if (!viewer) return;
     viewer.entities.removeAll(); // Completely destroys all entities on every events array change!
     events.forEach((evt) => { /* recreates entities */ });
   }, [events]);
   ```
   Every time a WebSocket message arrives or a filter tab changes, `viewer.entities.removeAll()` wipes the scene and reinstantiates every single `Cesium.Entity`, causing GC pressure and WebGL pipeline rebuilds.

2. **Continuous Render Loop**:
   By default, CesiumJS runs a continuous requestAnimationFrame rendering loop even when the camera is idle. `requestRenderMode` is currently set to `false` (default), keeping GPU usage high.

3. **React State Re-render Cascades**:
   In `frontend/src/App.tsx`, incoming WebSocket messages update the `events` state array without component memoization (`React.memo`), causing `Header`, `FilterPanel`, `GlobeViewer`, and `EventDetailDrawer` to all re-render concurrently.

### Proposed Technical Solution & Action Items
- [ ] **Enable Explicit Render Mode in Cesium**:
  In `GlobeViewer.tsx` initialization:
  ```typescript
  const viewer = new Cesium.Viewer(containerRef.current, {
    requestRenderMode: true,
    maximumRenderTimeChange: 0.0,
    // ...
  });
  ```
  Call `viewer.scene.requestRender()` whenever entities or camera destinations update.

- [ ] **In-Place Entity Updates via Map Cache**:
  Replace `viewer.entities.removeAll()` with a persistent `Map<string, Cesium.Entity>` stored in a React `useRef`. Update existing entity position/color in-place, add new entities, and remove deleted ones.

- [ ] **Memoize React Components**:
  Wrap `GlobeViewer` and `FilterPanel` in `React.memo` to prevent unnecessary re-renders when unrelated parent state changes.

### Acceptance Criteria
- [ ] Cesium frame rate stays at 60 FPS during camera flyTo animations.
- [ ] Adding or updating a single event via WebSocket updates only the specific Cesium entity in $<5\text{ms}$ without clearing all entities.
- [ ] GPU load drops significantly when the map camera is stationary due to `requestRenderMode: true`.

---

## Issue 2: [BUG] Metric Counts Dynamically Fluctuate When Switching Filter Tabs

### Metadata
- **Title**: `[BUG] Metric Counts Dynamically Fluctuate When Switching Filter Tabs`
- **Labels**: `bug`, `frontend`, `backend`, `analytics`
- **Priority**: **Medium**
- **Affected Area**: `frontend/src/components/FilterPanel.tsx`, `frontend/src/App.tsx`, `backend/app/api/v1/endpoints/events.py`

### Problem Description & Current Behavior
The quick metrics summary cards in `FilterPanel.tsx` (**High**, **Medium**, **Low**) dynamically drop to zero or change incorrectly when an analyst clicks on a specific threat filter tab. For example, selecting the "High" tab sets `High` to 5, while `Medium` and `Low` drop to 0, despite active medium and low events existing in the database.

### Expected Behavior
The metric summary cards should display the **global collection counts** (e.g. Total: 40, High: 10, Medium: 20, Low: 10) regardless of which specific view filter tab (All, High, Medium, Low) is currently selected.

### Root Cause Analysis
1. In `FilterPanel.tsx`:
   ```typescript
   const highCount = events.filter((e) => e.threat_level === 'High').length;
   const medCount = events.filter((e) => e.threat_level === 'Medium').length;
   const lowCount = events.filter((e) => e.threat_level === 'Low').length;
   ```
2. When the user clicks the "High" tab, `onFilterChange({ threat_level: 'High' })` triggers an API fetch: `GET /api/v1/events?threat_level=High`.
3. The backend returns an `events` array containing *only* High threat events.
4. `FilterPanel` computes `medCount` and `lowCount` against this filtered `events` subset, yielding `0` for both.

### Proposed Technical Solution & Action Items
- [ ] **Create Dedicated Analytics Stats Endpoint**:
  Add `GET /api/v1/events/stats` in `backend/app/api/v1/endpoints/events.py`:
  ```python
  @router.get("/stats", response_model=EventStatsResponse)
  async def get_event_stats():
      # Returns global counts: {"total": 40, "high": 10, "medium": 20, "low": 10}
  ```
- [ ] **Update Frontend State Architecture**:
  In `App.tsx`, fetch global event stats independently via `getEventStats()` and pass `globalStats` to `FilterPanel` so summary cards remain static regardless of active tab filters.

### Acceptance Criteria
- [ ] Selecting "High", "Med", or "Low" tabs does not change the numbers displayed inside the quick stats metric cards.
- [ ] Summary counts reflect accurate database totals upon page load and after pipeline execution.

---

## Issue 3: [NLP/DATA] Irrelevant General News Ingested as Security Threats (Threat Relevance Filtering)

### Metadata
- **Title**: `[NLP/DATA] Irrelevant General News Ingested as Security Threats (Threat Relevance Filtering)`
- **Labels**: `bug`, `nlp`, `ingestion`, `intelligence`
- **Priority**: **High**
- **Affected Area**: `backend/app/ingestion/rss_collector.py`, `backend/app/nlp/preprocessing.py`, `backend/app/intelligence/threat_scorer.py`

### Problem Description & Current Behavior
General news articles (e.g. sports tournaments, local economy updates, entertainment awards, general elections) collected from public RSS feeds are currently ingested, run through NLP, assigned non-zero threat scores, and plotted as events on the 3D globe.

### Expected Behavior
Only reports with genuine security, defense, conflict, military asset, or emergency context should be scored as active threat events. Non-security news items should either be discarded at the ingestion stage or marked with `threat_score = 0.0` and excluded from map markers.

### Root Cause Analysis
1. In `backend/app/ingestion/rss_collector.py`, all RSS feed entries are ingested indiscriminately without a domain relevance filter.
2. In `backend/app/intelligence/threat_scorer.py`:
   ```python
   location_score = DEFAULT_LOCATION_SENSITIVITY # Defaults to 5.0 points even if no security entity exists!
   ```
   Even if an article contains zero security keywords (`action_score = 0`, `equipment_score = 0`), `threat_scorer.py` still assigns default location points (5.0) and frequency points, producing a total threat score $>0$ and saving it as a "Low" threat event.

### Proposed Technical Solution & Action Items
- [ ] **Implement Security Relevance Classifier/Gatekeeper**:
  In `backend/app/nlp/preprocessing.py` or `backend/app/nlp/service.py`, add `is_security_relevant(text, nlp_result)`:
  - Check if text contains at least one match from security/defense domain keywords (`military`, `defense`, `attack`, `missile`, `explosion`, `armed`, `conflict`, `casualty`, `security`, `forces`, `troop`, `drone`, `airstrike`, etc.) or custom `EntityRuler` patterns.
- [ ] **Update Threat Scorer Zero-Baseline**:
  In `threat_scorer.py`, if `found_actions` is empty AND `found_eq` is empty AND no security keywords exist, set `action_score = 0`, `equipment_score = 0`, `location_score = 0`, yielding `total = 0.0`.
- [ ] **Filter Non-Threats in Ingestion Pipeline**:
  Mark raw posts with zero security relevance as `processing_status = "non_threat"` and skip event creation.

### Acceptance Criteria
- [ ] General news articles (e.g. sports scores, financial stock updates) receive a `threat_score` of `0.0` and are not displayed on the 3D globe.
- [ ] Genuine conflict and security reports continue to be accurately extracted, scored, and plotted.

---

## Issue 4: [FEAT] Expand OSINT Ingestion to Multi-Source Public Feeds

### Metadata
- **Title**: `[FEAT] Expand OSINT Ingestion to Multi-Source Public Feeds`
- **Labels**: `enhancement`, `ingestion`, `backend`, `data`
- **Priority**: **Medium**
- **Affected Area**: `backend/app/ingestion/config.py`, `backend/app/ingestion/rss_collector.py`, `backend/app/intelligence/config.py`

### Problem Description & Current Behavior
The ingestion configuration in `backend/app/ingestion/config.py` currently relies on a minimal list of general news RSS feeds (e.g. BBC, Al Jazeera, UN News). This restricts intelligence coverage and limits testing of the multi-source independent corroboration logic in `credibility_scorer.py`.

### Expected Behavior
ThreatAtlas should monitor a diverse, reliable set of public OSINT, geopolitical conflict, defense, and international humanitarian RSS feeds with pre-configured source reliability ratings.

### Root Cause Analysis
The feed dictionary in `backend/app/ingestion/config.py` was created as an initial MVP template and has not yet been expanded with dedicated military/security data sources.

### Proposed Technical Solution & Action Items
- [ ] **Expand Feed Registry in `backend/app/ingestion/config.py`**:
  Add curated public RSS endpoints:
  - **Defense News**: `https://www.defensenews.com/arc/outboundfeeds/rss/`
  - **Reuters World**: `https://www.reutersagency.com/feed/?best-topics=world-news`
  - **ReliefWeb Crisis Reports**: `https://reliefweb.int/updates/rss.xml`
  - **US Naval Institute News**: `https://news.usni.org/feed`
  - **UK MOD / Security Announcements**: `https://www.gov.uk/government/organisations/ministry-of-defence.atom`
- [ ] **Update Source Reliability Map**:
  In `backend/app/intelligence/config.py`, assign `SOURCE_RELIABILITY_MAP` entries for newly added sources (e.g. `defensenews`: 85.0, `reliefweb`: 90.0, `usni news`: 85.0).

### Acceptance Criteria
- [ ] Running `POST /api/v1/ingestion/rss` fetches and normalizes posts from multiple international defense and security feeds.
- [ ] Multi-source corroboration tests in `test_intelligence.py` verify that independent reports from distinct defense feeds boost the event `credibility_score`.

---

## Issue 5: [BUG] Inconsistent 3D Globe Point Clickability and Hit-Testing

### Metadata
- **Title**: `[BUG] Inconsistent 3D Globe Point Clickability and Hit-Testing`
- **Labels**: `bug`, `frontend`, `cesium`, `ui/ux`
- **Priority**: **Medium**
- **Affected Area**: `frontend/src/components/GlobeViewer.tsx`

### Problem Description & Current Behavior
Clicking on threat markers on the 3D globe is sometimes unreliable. Certain point markers do not trigger the `ScreenSpaceEventHandler` `LEFT_CLICK` event, failing to open the `EventDetailDrawer` or execute camera `flyTo`.

### Expected Behavior
Clicking anywhere on or near a threat marker (within a generous pixel pick radius) should reliably select the event, highlight the marker, and open the `EventDetailDrawer`.

### Root Cause Analysis
1. In `GlobeViewer.tsx`:
   ```typescript
   const pickedObject = scene.pick(movement.position);
   ```
   Cesium's `scene.pick` performs single-pixel raycasting. For small point entities (`pixelSize: 10`), the clickable target area is only 10x10 screen pixels, making hit-testing difficult on high-DPI/Retina screens.
2. When multiple event markers exist at identical or close geographic coordinates, `scene.pick` returns only the top-most primitive without giving the user a choice or disambiguation list.

### Proposed Technical Solution & Action Items
- [ ] **Add Billboard Pick Buffer / Increase Hit Radius**:
  Combine `point` styling with a transparent or padded `billboard` icon or set a minimum `pixelSize` of `14` with a larger `outlineWidth` to expand the raycast pick area.
- [ ] **Implement `scene.drillPick` for Overlapping Markers**:
  In `GlobeViewer.tsx`:
  ```typescript
  const pickedObjects = scene.drillPick(movement.position);
  if (pickedObjects && pickedObjects.length > 0) {
    // Extract all event IDs at click location
    // If len > 1, open disambiguation list; if 1, select immediately
  }
  ```

### Acceptance Criteria
- [ ] Threat markers respond instantly to clicks anywhere within a 20px radius of the point.
- [ ] Clicking overlapping event markers displays a clean selection list allowing the analyst to pick the target event.

---

## Issue 6: [ENHANCEMENT] Configurable Threat Score Threshold Filter for 3D Globe Display

### Metadata
- **Title**: `[ENHANCEMENT] Configurable Threat Score Threshold Filter for 3D Globe Display`
- **Labels**: `enhancement`, `frontend`, `backend`, `ui/ux`
- **Priority**: **Medium**
- **Affected Area**: `frontend/src/components/FilterPanel.tsx`, `frontend/src/components/GlobeViewer.tsx`, `frontend/src/api/client.ts`, `backend/app/api/v1/endpoints/events.py`

### Problem Description & Current Behavior
Low-threat or low-severity events can clutter the 3D globe viewport. Analysts currently have to toggle between "High", "Med", or "Low" tabs, but cannot set a fine-grained minimum threat score threshold (e.g. show only events with `threat_score >= 50.0`).

### Expected Behavior
The sidebar filter panel should include a "Minimum Threat Score" range slider (0 to 100) and a "Hide Low Severity on Map" toggle button that dynamically filters map markers.

### Root Cause Analysis
The backend endpoint `GET /api/v1/events` already supports `min_threat_score: float` in `backend/app/api/v1/endpoints/events.py`, but the frontend `FilterPanel.tsx` has no UI control bound to this parameter.

### Proposed Technical Solution & Action Items
- [ ] **Add Slider & Toggle Controls in `FilterPanel.tsx`**:
  - Add a Range Input slider (`min=0`, `max=100`, `step=5`) bound to `filters.min_threat_score`.
  - Add a quick toggle: `Hide Low Threat (<40)`.
- [ ] **Pass `min_threat_score` to API Client**:
  In `frontend/src/api/client.ts`, pass `min_threat_score` in query params during `fetchEvents(filters)`.
- [ ] **Dynamic Globe Marker Refresh**:
  When the slider changes, `GlobeViewer` updates entities to reflect only events satisfying `evt.threat_score >= min_threat_score`.

### Acceptance Criteria
- [ ] Moving the slider to `50` hides all events with a threat score below 50 from both the sidebar list and 3D globe markers.
- [ ] The current threshold value is displayed clearly in the UI (e.g. `Min Score: 50/100`).
