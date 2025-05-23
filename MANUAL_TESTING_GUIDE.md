# Manual Testing Guide: PUBG Stats Dashboard

This document outlines manual test cases for the PUBG Stats Dashboard application.

**Tester:** _________________________
**Date:** _________________________
**Environment:** (e.g., Local Development, Staging) _________________________
**Browser(s) Tested:** _________________________

---

## 1. Individual Player Stats

**Test Case ID:** TC_IND_001
**Feature:** Individual Weapon Stats - Valid Player and Season
**Preconditions:**
    *   A known valid PUBG player name (e.g., "TGLTN", or a test account with known data).
    *   A known platform for that player (e.g., "Steam").
    *   A known season ID where the player has played matches and has weapon stats (e.g., a recent PC season ID like "division.bro.official.steam-2023-10").
**Steps to Execute:**
    1.  Navigate to the application UI (e.g., `/ui/index.html`).
    2.  Enter the valid player name in the "Player Name" field.
    3.  Select the correct platform from the "Platform" dropdown.
    4.  Enter the valid season ID in the "Season ID" field.
    5.  Click the "Get Stats" button.
**Expected Result:**
    *   Loading indicator appears while data is fetched.
    *   The "Weapon Stats for [PlayerName] ([Platform]) - Season [SeasonID]" section appears.
    *   "Total Matches Played in Season (for weapon stats)" is displayed with a number.
    *   For weapon categories where the player has stats (AR, SR, DMR, SMG, Shotgun), a card appears showing:
        *   "Top [CategoryName]" (e.g., "Top AR").
        *   "Weapon:" with the name of the top weapon in that category.
        *   "Total Damage:", "Kills:", "Damage Per Match (DPM):" with calculated values.
    *   DPM should be `Total Damage / Total Matches Played in Season`.
    *   UI elements match the application theme.
    *   No errors displayed in the main error area or console.
**Actual Result:**
**Pass/Fail:**

---

**Test Case ID:** TC_IND_002
**Feature:** Individual Weapon Stats - Player Not Found
**Preconditions:**
    *   An invalid or non-existent PUBG player name (e.g., "ThisPlayerDoesNotExist12345").
    *   Any valid platform and season ID.
**Steps to Execute:**
    1.  Navigate to the application UI.
    2.  Enter the invalid player name.
    3.  Select a platform.
    4.  Enter a season ID.
    5.  Click "Get Stats".
**Expected Result:**
    *   Loading indicator appears and then disappears.
    *   An error message is displayed in the main error area (below "Results") indicating "Player '[InvalidName]' not found..." or similar.
    *   No weapon stats are displayed.
    *   Team Performance and Overall Team Stats sections might also show errors or messages indicating player data is unavailable.
**Actual Result:**
**Pass/Fail:**

---

**Test Case ID:** TC_IND_003
**Feature:** Individual Weapon Stats - Season With No Stats / Invalid Season
**Preconditions:**
    *   A valid PUBG player name and platform.
    *   A season ID for which the player has no recorded stats, or an invalid/malformed season ID.
**Steps to Execute:**
    1.  Navigate to the application UI.
    2.  Enter the valid player name and platform.
    3.  Enter the no-stats/invalid season ID.
    4.  Click "Get Stats".
**Expected Result:**
    *   Loading indicator appears and then disappears.
    *   An error message related to the season not being found or having no data (e.g., "Season 'X' not found for player 'Y'...") should appear in the main error area.
    *   Alternatively, "Total Matches Played in Season" might be 0, and "No weapon stats found..." message appears under Weapon Stats.
    *   Other sections should reflect the unavailability of data.
**Actual Result:**
**Pass/Fail:**

---

**Test Case ID:** TC_IND_004
**Feature:** Individual Weapon Stats - Partial Weapon Category Stats
**Preconditions:**
    *   A player and season where they have stats for some primary weapon categories (e.g., ARs) but not others (e.g., no SR usage).
**Steps to Execute:**
    1.  Enter player name, platform, and season ID.
    2.  Click "Get Stats".
**Expected Result:**
    *   Weapon stat cards appear only for categories where the player has data.
    *   For categories with no data, no card is shown.
    *   "Total Matches Played" is displayed correctly.
**Actual Result:**
**Pass/Fail:**

---

**Test Case ID:** TC_IND_005
**Feature:** Individual Weapon Stats - Platform Selection (Kakao)
**Preconditions:**
    *   A known valid PUBG player name on the Kakao platform.
    *   A known valid season ID for Kakao.
**Steps to Execute:**
    1.  Enter Kakao player name.
    2.  Select "Kakao" from the "Platform" dropdown.
    3.  Enter Kakao season ID.
    4.  Click "Get Stats".
**Expected Result:**
    *   Stats for the Kakao player are displayed correctly.
    *   Platform in the results header shows "Kakao".
**Actual Result:**
**Pass/Fail:**

---

## 2. Team Identification & Performance Comparison

**Test Case ID:** TC_TEAM_001
**Feature:** Team Sections - Player in Active Clan
**Preconditions:**
    *   Player name known to be in an active clan, and plays frequently with clan members.
    *   Valid platform and a recent season ID.
**Steps to Execute:**
    1.  Enter player name, platform, and season ID.
    2.  Click "Get Stats".
**Expected Result:**
    *   After individual stats, the "Team Performance Comparison" section appears.
    *   Team Identification Message indicates team identified by "clan membership" and shows play frequency.
    *   Radar charts are displayed for clan teammates (excluding the main player).
    *   Chart data (Avg Kills, Damage, etc.) appears reasonable for each teammate. (Spot check one teammate if possible by looking up their recent matches with the main player via external sites, if feasible, or just check for sensible numbers).
    *   "Overall Team Stats" section shows stats for when the full clan team played together.
**Actual Result:**
**Pass/Fail:**

---

**Test Case ID:** TC_TEAM_002
**Feature:** Team Sections - Player with Frequent Non-Clan Team
**Preconditions:**
    *   Player name known to *not* be in a clan, or in an inactive clan, but plays frequently with a consistent group of non-clan members.
    *   Valid platform and a recent season ID.
**Steps to Execute:**
    1.  Enter player name, platform, and season ID.
    2.  Click "Get Stats".
**Expected Result:**
    *   "Team Performance Comparison" section appears.
    *   Team Identification Message indicates team identified by "frequent squad" and shows play frequency.
    *   Radar charts for the frequent squad members are displayed.
    *   "Overall Team Stats" section shows stats for when this frequent squad played together.
**Actual Result:**
**Pass/Fail:**

---

**Test Case ID:** TC_TEAM_003
**Feature:** Team Sections - Player with Clan and More Frequent Non-Clan Team
**Preconditions:**
    *   Player is in a clan but plays *more* frequently and consistently with a non-clan squad.
    *   Valid platform and a recent season ID.
**Steps to Execute:**
    1.  Enter player name, platform, and season ID.
    2.  Click "Get Stats".
**Expected Result:**
    *   "Team Performance Comparison" section appears.
    *   Team Identification Message indicates team identified by "frequent squad" (due to higher play frequency than clan).
    *   Radar charts for the non-clan squad members are displayed.
    *   "Overall Team Stats" section shows stats for this frequent squad.
**Actual Result:**
**Pass/Fail:**

---

**Test Case ID:** TC_TEAM_004
**Feature:** Team Sections - Player with No Clear Team
**Preconditions:**
    *   Player name who plays mostly solo or with many different random players, not meeting frequency thresholds for clan or squad.
    *   Valid platform and a recent season ID.
**Steps to Execute:**
    1.  Enter player name, platform, and season ID.
    2.  Click "Get Stats".
**Expected Result:**
    *   "Team Performance Comparison" section appears.
    *   Team Identification Message indicates "No consistent team identified..." or similar.
    *   Team Charts Container shows a message like "No team performance data to display..."
    *   "Overall Team Stats" section message indicates "No recent matches found where the identified team played together..." or "No valid team identified..."
**Actual Result:**
**Pass/Fail:**

---

## 3. Overall Team Stats

**Test Case ID:** TC_OTS_001
**Feature:** Overall Team Stats - Full Team Plays Together
**Preconditions:**
    *   Use a player from TC_TEAM_001 or TC_TEAM_002 where a team is identified and known to play together.
**Steps to Execute:**
    1.  Enter relevant player name, platform, and season ID.
    2.  Click "Get Stats".
    3.  Scroll to the "Overall Team Stats" section.
**Expected Result:**
    *   The message indicates stats are based on a number of matches played as a full team.
    *   "Average Team Kills per Match", "Average Team Damage per Match", "Average Team Survival Time", and "Average Team Match Rank" are displayed with numerical values.
    *   Values appear reasonable based on team size and general expectations.
**Actual Result:**
**Pass/Fail:**

---

**Test Case ID:** TC_OTS_002
**Feature:** Overall Team Stats - Team Rarely Plays as Full Unit
**Preconditions:**
    *   An identified team that (based on the last `NUM_MATCHES_TO_ANALYZE`) has few or zero matches where *all* members played together.
**Steps to Execute:**
    1.  Enter relevant player name, platform, and season ID.
    2.  Click "Get Stats".
    3.  Scroll to the "Overall Team Stats" section.
**Expected Result:**
    *   The message indicates "No recent matches found where the identified team played together as a full unit" or that stats are based on a very small number of matches (e.g., < `MIN_GAMES_FOR_FREQUENT_TEAM`).
    *   If 0 matches as full team, stats should be 0.0.
**Actual Result:**
**Pass/Fail:**

---

## 4. UI & UX

**Test Case ID:** TC_UI_001
**Feature:** UI - Responsiveness
**Preconditions:** None.
**Steps to Execute:**
    1.  Load the application in a desktop browser.
    2.  Gradually resize the browser window from wide to narrow (simulating mobile width).
    3.  Observe layout changes, especially for the input form, stats cards, and chart containers.
**Expected Result:**
    *   Content remains readable and accessible at narrower widths.
    *   Elements stack or resize appropriately (e.g., charts per row).
    *   No major layout breaks or horizontal scrolling on the main container.
**Actual Result:**
**Pass/Fail:**

---

**Test Case ID:** TC_UI_002
**Feature:** UI - Loading Indicators
**Preconditions:** Any valid or invalid input that triggers data fetching.
**Steps to Execute:**
    1.  Enter player data and click "Get Stats".
    2.  Observe the loading indicator.
**Expected Result:**
    *   The CSS spinner loading indicator appears promptly after clicking "Get Stats".
    *   The indicator remains visible while data is being fetched for all sections.
    *   The indicator disappears once all data is loaded or all errors are displayed.
**Actual Result:**
**Pass/Fail:**

---

**Test Case ID:** TC_UI_003
**Feature:** UI - Error Message Display
**Preconditions:** Use inputs from TC_IND_002 (Player Not Found) or TC_IND_003 (Invalid Season).
**Steps to Execute:**
    1.  Trigger an error scenario.
**Expected Result:**
    *   Error messages are displayed in the correct section (e.g., main error display, team error display).
    *   Messages are user-friendly (e.g., "Player 'X' not found..." not just "404 Error").
    *   Error messages are styled consistently with the theme (red accents, etc.).
    *   Error messages clear when a new search is initiated.
**Actual Result:**
**Pass/Fail:**

---

**Test Case ID:** TC_UI_004
**Feature:** UI - Caching Behavior (Conceptual)
**Preconditions:** Valid player name, platform, season.
**Steps to Execute:**
    1.  Enter player details and click "Get Stats". Note the time taken (subjective).
    2.  Without changing inputs, click "Get Stats" again immediately.
    3.  Note the time taken. It should be significantly faster.
    4.  Change the Season ID to a different valid season for the same player. Click "Get Stats". Note time.
    5.  Change back to the original Season ID. Click "Get Stats". Should be fast again (from cache).
    6.  (Harder to test precisely) Wait for cache TTL to expire (e.g., 30 mins for seasonal stats, 1 hour for player ID) and try again. It should fetch fresh data.
**Expected Result:**
    *   Subsequent identical requests are faster due to caching.
    *   Requests with different parameters (e.g., different season ID) fetch new data initially but are then cached.
    *   Data updates after TTL expiry (this is hard to verify precisely in manual testing without tools).
**Actual Result:**
**Pass/Fail:**

---

**Test Case ID:** TC_UI_005
**Feature:** UI - Theme Consistency
**Preconditions:** None.
**Steps to Execute:**
    1.  Navigate through all sections of the application after performing a full data fetch.
    2.  Observe fonts, colors, spacing, button styles, card styles.
**Expected Result:**
    *   The "Teko" font is used consistently.
    *   The dark theme with yellow/gold accents is applied throughout.
    *   UI elements (buttons, inputs, cards) have a consistent look and feel.
**Actual Result:**
**Pass/Fail:**

---

## 5. Edge Cases

**Test Case ID:** TC_EDGE_001
**Feature:** Input - Special Characters
**Preconditions:** None.
**Steps to Execute:**
    1.  In "Player Name", enter names with common special characters (e.g., "Player-One", "Player_Two", "Player.Test").
    2.  In "Season ID", enter a valid season ID.
    3.  Click "Get Stats".
**Expected Result:**
    *   If the characters are valid for PUBG names/season IDs, the search proceeds.
    *   If characters are invalid, client-side validation (if implemented for those specific chars) or backend API should return a user-friendly error (e.g., "Invalid characters in player name"). The application should not crash.
    *   (Note: Current client-side validation is basic for player name).
**Actual Result:**
**Pass/Fail:**

---

**Test Case ID:** TC_EDGE_002
**Feature:** Input - Long Strings
**Preconditions:** None.
**Steps to Execute:**
    1.  Enter a very long string (e.g., 50+ characters) for "Player Name".
    2.  Enter a very long string for "Season ID".
    3.  Click "Get Stats".
**Expected Result:**
    *   Client-side validation might catch overly long player names (current check is 2-20 chars).
    *   If it passes client-side, the backend should handle it gracefully, likely resulting in a "Player Not Found" or "Invalid Season" error from the PUBG API.
    *   The UI should not break due to long input strings.
**Actual Result:**
**Pass/Fail:**

---

**Test Case ID:** TC_EDGE_003
**Feature:** UI - Rapid Interactions
**Preconditions:** None.
**Steps to Execute:**
    1.  Quickly change input values and click "Get Stats" multiple times in succession.
    2.  Try to trigger multiple fetch requests.
**Expected Result:**
    *   The application should handle multiple requests gracefully.
    *   Loading indicators should behave correctly.
    *   The UI should eventually settle and display results/errors for the latest valid request or manage concurrent requests without crashing. (Rate limiting on the backend might also be triggered by the external API).
**Actual Result:**
**Pass/Fail:**

---
