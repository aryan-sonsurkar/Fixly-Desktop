# Fixly Desktop — Manual Beta Test Plan

**Version:** 1.0  
**Date:** 2026-09-11  
**Testers:** Hiba, Aarya  
**Platform:** Windows  

---

## Instructions

1. Complete each test case in order.
2. Fill in **Actual result**, **PASS / FAIL**, and **Notes** for every test case.
3. If a test fails, attach a screenshot or log in the Notes column.
4. Report all issues to the team channel with the test ID.

---

## 1. Installation / Startup

### T001 — Fresh Install
| Field | Content |
|---|---|
| **Purpose** | Verify the app installs without errors on a clean machine. |
| **Steps** | 1. Download the latest `.exe` installer. 2. Double-click the installer. 3. Follow the setup wizard. 4. Finish installation. |
| **Expected result** | Installer completes successfully. Fixly shortcut appears on desktop and Start menu. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T002 — App Icon Verification
| Field | Content |
|---|---|
| **Purpose** | Verify the app icon displays correctly. |
| **Steps** | 1. Locate the Fixly shortcut on the desktop. 2. Locate the Fixly entry in the Start menu. 3. Observe the icon in both locations. |
| **Expected result** | The Fixly icon renders clearly at all standard sizes (16×16, 32×32, 48×48). |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T003 — Cold Start vs Warm Start
| Field | Content |
|---|---|
| **Purpose** | Verify the app starts quickly and loads the dashboard on both cold and warm launches. |
| **Steps** | 1. Close the app completely. 2. Launch the app (cold start). 3. Note the time to reach the dashboard. 4. Close the app. 5. Launch again (warm start). 6. Note the time to reach the dashboard. |
| **Expected result** | Cold start reaches the dashboard in under 10 seconds. Warm start is faster than cold start. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

---

## 2. Login / Account

### T004 — Register New Account
| Field | Content |
|---|---|
| **Purpose** | Verify a new user can register successfully. |
| **Steps** | 1. Launch the app. 2. Click "Sign Up". 3. Enter a valid email and password. 4. Click "Create Account". |
| **Expected result** | Account is created. User is redirected to the onboarding or dashboard screen. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T005 — Login with Existing Account
| Field | Content |
|---|---|
| **Purpose** | Verify an existing user can log in. |
| **Steps** | 1. Launch the app. 2. Enter registered email and password. 3. Click "Log In". |
| **Expected result** | User is authenticated and reaches the dashboard. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T006 — Profile Page
| Field | Content |
|---|---|
| **Purpose** | Verify the profile page loads and displays the correct user information. |
| **Steps** | 1. Log in. 2. Click on the profile icon or navigate to the profile page. 3. Verify name, email, and avatar are displayed. |
| **Expected result** | Profile page renders with all user details correctly populated. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

---

## 3. Documents / Indexing

### T007 — Upload PDF Document
| Field | Content |
|---|---|
| **Purpose** | Verify a PDF can be uploaded and indexed. |
| **Steps** | 1. Navigate to the Documents section. 2. Click "Upload". 3. Select a PDF file (under 25 MB). 4. Wait for upload to complete. |
| **Expected result** | Upload completes. The document appears in the document list with a "indexed" status. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T008 — Verify Indexing Status
| Field | Content |
|---|---|
| **Purpose** | Verify the uploaded document is fully indexed and searchable. |
| **Steps** | 1. Open the Documents section. 2. Locate the recently uploaded PDF. 3. Check the status indicator. |
| **Expected result** | Document status shows "Indexed" (not "Pending" or "Error"). |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T009 — Search Within Documents
| Field | Content |
|---|---|
| **Purpose** | Verify the document search returns accurate results. |
| **Steps** | 1. Open the search bar. 2. Type a keyword that exists in the uploaded PDF. 3. Observe the results. |
| **Expected result** | Search results include the uploaded document and highlight the matching keyword. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T010 — Delete Document
| Field | Content |
|---|---|
| **Purpose** | Verify a document can be deleted and removed from the index. |
| **Steps** | 1. Navigate to the Documents section. 2. Select the uploaded PDF. 3. Click "Delete". 4. Confirm deletion. |
| **Expected result** | Document is removed from the list. Searching for it returns no results. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

---

## 4. RAG / Citations

### T011 — Ask Question About Uploaded Document
| Field | Content |
|---|---|
| **Purpose** | Verify the AI can answer a question based on the content of an uploaded document. |
| **Steps** | 1. Upload a PDF with known content. 2. Open the AI chat. 3. Ask a question whose answer is in the document. 4. Read the AI response. |
| **Expected result** | The AI provides an answer derived from the document content. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T012 — Verify Citations Are Shown
| Field | Content |
|---|---|
| **Purpose** | Verify that AI responses include citations pointing to the source document. |
| **Steps** | 1. Ask a question about an uploaded document. 2. Inspect the AI response for citation links or references. |
| **Expected result** | The response includes at least one citation (file name, page number, or link). |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T013 — Verify Source Accuracy
| Field | Content |
|---|---|
| **Purpose** | Verify that the cited source matches the actual content in the document. |
| **Steps** | 1. Ask a question about an uploaded document. 2. Open the cited source. 3. Compare the AI answer with the source content. |
| **Expected result** | The AI's answer is factually consistent with the cited source. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

---

## 5. Memory

### T014 — Give a Preference
| Field | Content |
|---|---|
| **Purpose** | Verify the AI stores a user-stated preference. |
| **Steps** | 1. Open the AI chat. 2. Say "I prefer studying in the morning." 3. Wait for the AI to acknowledge. |
| **Expected result** | The AI confirms the preference has been saved or acknowledges it. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T015 — Verify Memory in Next Conversation
| Field | Content |
|---|---|
| **Purpose** | Verify the AI recalls the saved preference in a new conversation. |
| **Steps** | 1. Start a new chat session. 2. Ask "What time of day do I prefer to study?" |
| **Expected result** | The AI responds with the previously stated preference (morning). |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T016 — Memory Persistence After Restart
| Field | Content |
|---|---|
| **Purpose** | Verify saved memories persist after the app is restarted. |
| **Steps** | 1. Restart the app completely. 2. Open a new chat. 3. Ask about the saved preference. |
| **Expected result** | The AI still recalls the preference after restart. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T017 — Edit or Delete Memory
| Field | Content |
|---|---|
| **Purpose** | Verify a user can edit or delete a saved memory. |
| **Steps** | 1. Navigate to the Memory or Settings section. 2. Locate the saved preference. 3. Edit or delete it. 4. Verify the change in a new chat. |
| **Expected result** | The edited or deleted memory is no longer referenced by the AI. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

---

## 6. Workspace Context

### T018 — Ask About Due Items This Week
| Field | Content |
|---|---|
| **Purpose** | Verify the AI can pull real data from the user's workspace. |
| **Steps** | 1. Open the AI chat. 2. Ask "What do I have due this week?" 3. Review the response. |
| **Expected result** | The AI lists actual assignments or deadlines from the user's workspace. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T019 — Verify Real Data Shown
| Field | Content |
|---|---|
| **Purpose** | Confirm the data returned matches what is actually in the workspace. |
| **Steps** | 1. Compare the AI's response with the Planners and Assignments sections. 2. Check each item listed. |
| **Expected result** | Every item in the AI response matches a real entry in the workspace. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T020 — Ask About Study Hours
| Field | Content |
|---|---|
| **Purpose** | Verify the AI can summarize study hour data. |
| **Steps** | 1. Open the AI chat. 2. Ask "How many hours have I studied this week?" 3. Review the response. |
| **Expected result** | The AI provides a summary of study hours based on logged or tracked data. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

---

## 7. Safe AI Actions

### T021 — Ask to Create Assignment
| Field | Content |
|---|---|
| **Purpose** | Verify the AI can create an assignment via chat. |
| **Steps** | 1. Open the AI chat. 2. Say "Create an assignment called 'Lab Report 3' due next Friday." 3. Wait for confirmation. |
| **Expected result** | The AI confirms creation. The assignment appears in the Assignments list. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T022 — Verify Assignment Created
| Field | Content |
|---|---|
| **Purpose** | Verify the assignment created by the AI exists and has correct details. |
| **Steps** | 1. Navigate to the Assignments section. 2. Locate the new assignment. 3. Verify the title and due date. |
| **Expected result** | Assignment "Lab Report 3" exists with the correct due date. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T023 — Ask to Add Planner Task
| Field | Content |
|---|---|
| **Purpose** | Verify the AI can add a task to the planner. |
| **Steps** | 1. Open the AI chat. 2. Say "Add a task: Read Chapter 5, scheduled for tomorrow." 3. Wait for confirmation. |
| **Expected result** | The AI confirms the task was added. The task appears in the Planner. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T024 — Ask to Start Pomodoro
| Field | Content |
|---|---|
| **Purpose** | Verify the AI can trigger the Pomodoro timer. |
| **Steps** | 1. Open the AI chat. 2. Say "Start a 25-minute Pomodoro session." 3. Observe the UI. |
| **Expected result** | The Pomodoro timer starts and displays 25 minutes. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

---

## 8. Risky Action Confirmation

### T025 — Ask to Delete Assignment
| Field | Content |
|---|---|
| **Purpose** | Verify the AI asks for confirmation before deleting an assignment. |
| **Steps** | 1. Create an assignment (if not already present). 2. Open the AI chat. 3. Say "Delete the assignment 'Lab Report 3'." |
| **Expected result** | The AI displays a confirmation dialog or asks for explicit confirmation before proceeding. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T026 — Verify Confirmation Dialog
| Field | Content |
|---|---|
| **Purpose** | Verify the confirmation dialog contains the correct details. |
| **Steps** | 1. Observe the confirmation prompt from T025. 2. Check that it mentions the assignment name. |
| **Expected result** | The dialog clearly states which assignment will be deleted and has Confirm/Cancel buttons. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T027 — Confirm and Verify Deletion
| Field | Content |
|---|---|
| **Purpose** | Verify confirming the dialog actually deletes the assignment. |
| **Steps** | 1. Click "Confirm" in the dialog. 2. Navigate to the Assignments section. 3. Search for the deleted assignment. |
| **Expected result** | The assignment is removed and no longer appears in the list. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

---

## 9. Multi-Step Workflow

### T028 — Ask for Study Plan Workflow
| Field | Content |
|---|---|
| **Purpose** | Verify the AI can execute a multi-step study plan workflow. |
| **Steps** | 1. Open the AI chat. 2. Ask "Create a study plan for my Physics midterm next week." 3. Follow the AI's prompts or let it proceed. |
| **Expected result** | The AI begins a multi-step workflow (e.g., gather context, create plan, present results). |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T029 — Verify Progress UI
| Field | Content |
|---|---|
| **Purpose** | Verify a progress indicator is shown during multi-step workflows. |
| **Steps** | 1. Start a workflow as in T028. 2. Observe the UI for a progress bar, step counter, or loading state. |
| **Expected result** | A visible progress indicator shows the current step or completion percentage. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T030 — Verify Final Result
| Field | Content |
|---|---|
| **Purpose** | Verify the workflow completes and delivers a usable result. |
| **Steps** | 1. Wait for the workflow to finish. 2. Review the output (study plan). |
| **Expected result** | A complete study plan is presented with tasks, dates, and study hours. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

---

## 10. Workflow Interruption / Resume

### T031 — Start and Interrupt Workflow
| Field | Content |
|---|---|
| **Purpose** | Verify workflow state is preserved when the app is closed mid-workflow. |
| **Steps** | 1. Start a multi-step workflow. 2. While it is running, close the app. 3. Reopen the app. |
| **Expected result** | The app closes without error. On reopen, the app recovers gracefully. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T032 — Verify State Preserved
| Field | Content |
|---|---|
| **Purpose** | Verify the interrupted workflow can be resumed or its partial result is available. |
| **Steps** | 1. After reopening from T031, navigate to the chat or workflow history. 2. Check if the previous workflow's context is available. |
| **Expected result** | The app shows the previous workflow state or allows the user to resume. No data is lost. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

---

## 11. Academic Profile

### T033 — View Academic Profile
| Field | Content |
|---|---|
| **Purpose** | Verify the academic profile page loads and shows correct data. |
| **Steps** | 1. Navigate to the Academic Profile section. 2. Verify subjects, grades, and overall summary are displayed. |
| **Expected result** | The page renders with all subjects, current scores, and a health indicator. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T034 — Add Score
| Field | Content |
|---|---|
| **Purpose** | Verify a new score can be added to a subject. |
| **Steps** | 1. Open Academic Profile. 2. Select a subject. 3. Click "Add Score". 4. Enter a score value and save. |
| **Expected result** | The new score is saved and reflected in the subject's data. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T035 — Verify Subject Health Shown
| Field | Content |
|---|---|
| **Purpose** | Verify each subject displays a health indicator. |
| **Steps** | 1. Open Academic Profile. 2. Observe the health indicator for each subject. |
| **Expected result** | Each subject shows a health status (e.g., Good, Needs Attention) based on scores. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

---

## 12. Goals / Skills / Roadmap

### T036 — Create Goal
| Field | Content |
|---|---|
| **Purpose** | Verify a user can create a new goal. |
| **Steps** | 1. Navigate to Goals. 2. Click "Create Goal". 3. Enter a title, description, and target date. 4. Save. |
| **Expected result** | The goal appears in the goals list with the correct details. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T037 — Set Goal Progress
| Field | Content |
|---|---|
| **Purpose** | Verify goal progress can be updated. |
| **Steps** | 1. Open the created goal. 2. Update the progress (e.g., 0% → 50%). 3. Save. |
| **Expected result** | The progress bar updates to reflect the new value. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T038 — Add Skill
| Field | Content |
|---|---|
| **Purpose** | Verify a user can add a skill to their profile. |
| **Steps** | 1. Navigate to Skills. 2. Click "Add Skill". 3. Enter a skill name and proficiency level. 4. Save. |
| **Expected result** | The skill appears in the skills list with the correct proficiency level. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T039 — Create Roadmap
| Field | Content |
|---|---|
| **Purpose** | Verify a user can create a roadmap. |
| **Steps** | 1. Navigate to Roadmaps. 2. Click "Create Roadmap". 3. Add milestones with titles and dates. 4. Save. |
| **Expected result** | The roadmap is created and displays milestones in chronological order. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

---

## 13. Opportunities

### T040 — Save Opportunity
| Field | Content |
|---|---|
| **Purpose** | Verify a user can save an opportunity. |
| **Steps** | 1. Navigate to Opportunities. 2. Click "Save Opportunity" or browse suggestions. 3. Save one. |
| **Expected result** | The opportunity appears in the saved list. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T041 — Change Opportunity Status
| Field | Content |
|---|---|
| **Purpose** | Verify the status of a saved opportunity can be updated. |
| **Steps** | 1. Open a saved opportunity. 2. Change its status (e.g., "Saved" → "Applied"). 3. Save. |
| **Expected result** | The status updates in the UI. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T042 — View Filtered List
| Field | Content |
|---|---|
| **Purpose** | Verify the opportunities list can be filtered by status. |
| **Steps** | 1. Navigate to Opportunities. 2. Apply a status filter (e.g., "Applied"). 3. Observe the results. |
| **Expected result** | Only opportunities matching the selected status are displayed. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

---

## 14. Proactive Insights

### T043 — Dashboard Shows Nudges
| Field | Content |
|---|---|
| **Purpose** | Verify the dashboard displays proactive nudges or suggestions. |
| **Steps** | 1. Open the dashboard. 2. Look for nudge cards (e.g., "Your Physics score dropped", "You have an assignment due"). |
| **Expected result** | At least one relevant nudge is displayed on the dashboard. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T044 — Dismiss Nudge
| Field | Content |
|---|---|
| **Purpose** | Verify a nudge can be dismissed. |
| **Steps** | 1. Locate a nudge on the dashboard. 2. Click the dismiss (X) button. |
| **Expected result** | The nudge is removed from the dashboard. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T045 — Verify No Duplicate Nudges
| Field | Content |
|---|---|
| **Purpose** | Verify the same nudge does not appear more than once. |
| **Steps** | 1. Open the dashboard. 2. Scan all visible nudges. 3. Check for duplicates. |
| **Expected result** | Each nudge is unique; no duplicates are present. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

---

## 15. Notifications

### T046 — Notifications Page Works
| Field | Content |
|---|---|
| **Purpose** | Verify the notifications page loads and lists notifications. |
| **Steps** | 1. Navigate to Notifications. 2. Verify the page loads. 3. Check that notifications are listed. |
| **Expected result** | The page renders with a list of notifications sorted by time. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T047 — Mark Notification as Read
| Field | Content |
|---|---|
| **Purpose** | Verify a notification can be marked as read. |
| **Steps** | 1. Open the Notifications page. 2. Click on an unread notification. 3. Verify its status changes to read. |
| **Expected result** | The notification's visual indicator (e.g., dot, bold text) is removed. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

---

## 16. Offline Mode

### T048 — Disconnect Internet and Launch App
| Field | Content |
|---|---|
| **Purpose** | Verify the app launches without an internet connection. |
| **Steps** | 1. Disconnect from the internet (Wi-Fi off, ethernet unplugged). 2. Launch the app. |
| **Expected result** | The app opens and displays a dashboard or offline indicator. It does not crash. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T049 — AI Responds Locally
| Field | Content |
|---|---|
| **Purpose** | Verify the AI chat works in offline mode. |
| **Steps** | 1. While offline, open the AI chat. 2. Ask a question. |
| **Expected result** | The AI provides a response using the local model. A message may indicate offline mode. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T050 — Document Search Works Offline
| Field | Content |
|---|---|
| **Purpose** | Verify document search functions without internet. |
| **Steps** | 1. While offline, open the search bar. 2. Search for a keyword in a previously indexed document. |
| **Expected result** | Search results are returned from locally indexed data. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

---

## 17. Reconnect / Synchronization

### T051 — Reconnect and Sync
| Field | Content |
|---|---|
| **Purpose** | Verify queued operations sync when the internet is restored. |
| **Steps** | 1. While offline, perform actions (e.g., add a task, save a document). 2. Reconnect to the internet. 3. Wait for sync to complete. |
| **Expected result** | A sync indicator appears. All queued operations are processed. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T052 — Verify No Duplicate Records
| Field | Content |
|---|---|
| **Purpose** | Verify sync does not create duplicate entries. |
| **Steps** | 1. After sync, navigate to the sections where offline actions were performed. 2. Count the records. |
| **Expected result** | Each action resulted in exactly one record. No duplicates exist. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

---

## 18. Web Retrieval

### T053 — Ask About Latest Information
| Field | Content |
|---|---|
| **Purpose** | Verify the AI can retrieve current information from the web. |
| **Steps** | 1. Ensure the internet is connected. 2. Open the AI chat. 3. Ask "What is the latest news about [topic]?" |
| **Expected result** | The AI provides a current and relevant response. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T054 — Verify Web Citation
| Field | Content |
|---|---|
| **Purpose** | Verify web-sourced answers include citations. |
| **Steps** | 1. Ask a web-retrieval question. 2. Inspect the response for citation links. |
| **Expected result** | The response includes URLs or source names for web-retrieved information. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T055 — Verify No Fake Sources
| Field | Content |
|---|---|
| **Purpose** | Verify cited web sources actually exist and are accessible. |
| **Steps** | 1. Open the cited URLs from T054 in a browser. 2. Verify the pages load and contain the referenced information. |
| **Expected result** | All cited sources are valid, accessible, and contain the claimed information. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

---

## 19. Model Switching

### T056 — Check AI Settings Page
| Field | Content |
|---|---|
| **Purpose** | Verify the AI settings page is accessible and shows model options. |
| **Steps** | 1. Navigate to Settings > AI. 2. Verify the available models are listed. |
| **Expected result** | The settings page displays model options with status indicators. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T057 — Verify Local Model Status
| Field | Content |
|---|---|
| **Purpose** | Verify the local model status is shown (loaded, loading, unavailable). |
| **Steps** | 1. Open Settings > AI. 2. Check the local model indicator. |
| **Expected result** | A clear status is shown (e.g., "Local model loaded" or "Downloading..."). |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

---

## 20. AI Reset

### T058 — Click Reset and Verify Confirmation
| Field | Content |
|---|---|
| **Purpose** | Verify the AI reset action requires confirmation. |
| **Steps** | 1. Navigate to Settings > AI. 2. Click "Reset". 3. Observe the confirmation dialog. |
| **Expected result** | A confirmation dialog appears warning that memories and context will be cleared. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T059 — Verify Memories Cleared
| Field | Content |
|---|---|
| **Purpose** | Verify the AI reset clears all saved memories. |
| **Steps** | 1. Confirm the reset in T058. 2. Open the AI chat. 3. Ask about a previously saved preference. |
| **Expected result** | The AI has no memory of previously saved preferences. It responds as a new user. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

---

## 21. Performance / Stability

### T060 — Measure Cold Start Time
| Field | Content |
|---|---|
| **Purpose** | Measure the time from app launch to dashboard ready (cold start). |
| **Steps** | 1. Close the app completely. 2. Open a stopwatch. 3. Launch the app. 4. Stop the timer when the dashboard is fully loaded. |
| **Expected result** | Cold start time is under 10 seconds. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T061 — Measure First AI Response Time
| Field | Content |
|---|---|
| **Purpose** | Measure the time from sending the first message to receiving the AI response. |
| **Steps** | 1. Open the AI chat. 2. Send a simple question. 3. Time the response. |
| **Expected result** | First response is received within 5 seconds (local model) or 10 seconds (cloud model). |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T062 — 30-Minute Stability Test
| Field | Content |
|---|---|
| **Purpose** | Verify the app remains stable during extended use. |
| **Steps** | 1. Use the app continuously for 30 minutes. 2. Switch between sections, chat with AI, upload documents, use timers. 3. Monitor for crashes or freezes. |
| **Expected result** | The app remains responsive with no crashes, freezes, or memory leaks for the full 30 minutes. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

---

## 22. Recovery / Error Handling

### T063 — Kill Backend Process
| Field | Content |
|---|---|
| **Purpose** | Verify the app handles a backend process crash gracefully. |
| **Steps** | 1. While the app is running, open Task Manager. 2. Find and end the Fixly backend process. 3. Observe the app's behavior. |
| **Expected result** | The app shows a user-friendly error message. It does not crash or become unresponsive. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T064 — Restart and Verify Recovery
| Field | Content |
|---|---|
| **Purpose** | Verify the app recovers fully after a backend crash. |
| **Steps** | 1. After T063, close the app. 2. Restart the app. 3. Verify all features work normally. |
| **Expected result** | The app restarts without issues. All data is intact. AI chat and other features work. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

### T065 — Test with Invalid Input
| Field | Content |
|---|---|
| **Purpose** | Verify the app handles invalid or unexpected input gracefully. |
| **Steps** | 1. In the AI chat, send empty messages, very long strings, special characters, and SQL-like input. 2. In forms, enter invalid data types (e.g., letters in a number field). |
| **Expected result** | The app does not crash. It shows appropriate validation messages or ignores invalid input. |
| **Actual result** | [blank] |
| **PASS / FAIL** | [blank] |
| **Notes** | [blank] |

---

## Summary

| Category | Total Tests | Pass | Fail | Blocked |
|---|---|---|---|---|
| 1. Installation / Startup | 3 | | | |
| 2. Login / Account | 3 | | | |
| 3. Documents / Indexing | 4 | | | |
| 4. RAG / Citations | 3 | | | |
| 5. Memory | 4 | | | |
| 6. Workspace Context | 3 | | | |
| 7. Safe AI Actions | 4 | | | |
| 8. Risky Action Confirmation | 3 | | | |
| 9. Multi-Step Workflow | 3 | | | |
| 10. Workflow Interruption / Resume | 2 | | | |
| 11. Academic Profile | 3 | | | |
| 12. Goals / Skills / Roadmap | 4 | | | |
| 13. Opportunities | 3 | | | |
| 14. Proactive Insights | 3 | | | |
| 15. Notifications | 2 | | | |
| 16. Offline Mode | 3 | | | |
| 17. Reconnect / Synchronization | 2 | | | |
| 18. Web Retrieval | 3 | | | |
| 19. Model Switching | 2 | | | |
| 20. AI Reset | 2 | | | |
| 21. Performance / Stability | 3 | | | |
| 22. Recovery / Error Handling | 3 | | | |
| **Total** | **65** | | | |

---

**Tested by:** ___________________  
**Reviewed by:** ___________________  
**Date:** ___________________
