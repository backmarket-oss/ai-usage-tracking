---
name: usage-tracking
description: Set up weekly CO2 emissions, cost, and model efficiency tracking for Claude Code. Run this to configure what you see, where, and how often. Re-run anytime to change your preferences.
---
<!-- category: data -->

# Weekly Cost & CO2 Tracker Setup

This skill runs an interactive onboarding to configure your Claude Code carbon & cost tracker. It installs a SessionStart hook and optional status bar based on your preferences.

## Onboarding protocol

Follow these steps exactly. Use the AskUserQuestion tool for each step, with previews so the user can see what each option looks like before choosing.

### Step 0: Check for existing config

Read `~/.claude/co2-tracker-config.json`. If it exists, show the current settings and ask:
> "You already have the tracker configured. Want to update your preferences or keep the current setup?"

If they want to keep it, stop here. Otherwise continue with Step 1.

### Step 1: What to track

Ask using AskUserQuestion with these options and previews:

- **Both (Recommended)** — Preview:
  ```
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Weekly Claude Report (past 7 days)
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    💰 Cost:      $902.47
    ⚡ Energy:    63.23 Wh
    🌍 CO2:       37.0g
    🔄 Tokens:    63.2M effective (217.3M raw)
    💾 Cache hit:  83% (saving ~71% compute)

    That's about:
      ☕ 1.8 cups of coffee (production)
      🔍 185.0 Google searches

    By model tier:
      Opus       $897.79 (99.5%)  ~34.1g CO2
      Haiku      $  3.97 ( 0.4%)  ~ 2.8g CO2

    What if you used a different model?
      Opus       $1018.83  (+9%)
      Sonnet     $ 203.77  (-78%)
      Haiku      $  54.34  (-94%)
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ```

- **Carbon footprint only** — Preview:
  ```
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Weekly Claude Report (past 7 days)
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    ⚡ Energy:    63.23 Wh
    🌍 CO2:       37.0g
    🔄 Tokens:    63.2M effective (217.3M raw)
    💾 Cache hit:  83% (saving ~71% compute)

    That's about:
      ☕ 1.8 cups of coffee (production)
      🔍 185.0 Google searches

    By model tier:
      Opus       ~34.1g CO2  [1363 calls]
      Haiku      ~ 2.8g CO2  [313 calls]
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ```

- **Cost only** — Preview:
  ```
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Weekly Claude Report (past 7 days)
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    💰 Cost:      $902.47
    🔄 Tokens:    63.2M effective (217.3M raw)
    💾 Cache hit:  83% (saving ~71% compute)

    By model tier:
      Opus       $897.79 (99.5%)  [1363 calls]
      Haiku      $  3.97 ( 0.4%)  [313 calls]
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ```

Map the answer: "Carbon footprint only" → `"co2"`, "Cost only" → `"cost"`, "Both" → `"both"`

### Step 2: Where to show it

Ask using AskUserQuestion with previews:

- **Both (Recommended)** — Preview:
  ```
  Welcome message (at session start):
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Weekly Claude Report (past 7 days)
    💰 $902  ⚡ 63 Wh  🌍 37g CO2
    ... (full breakdown)
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Status bar (live session stats, always visible):
  🌍 2.9g CO2 | 💰 $77.74 | [305 turns] | ☕ ~0.4 cups of coffee
  ```

- **Welcome message only** — Preview:
  ```
  Shows the full weekly report once
  when you start a new Claude Code
  session.

  No status bar.
  ```

- **Status bar only** — Preview:
  ```
  No welcome message at session start.

  Compact status bar (live session stats):

  🌍 2.9g CO2 | 💰 $77.74 | [305 turns] | ☕ ~0.4 cups of coffee
  ```

Map: "Welcome message only" → `"welcome"`, "Status bar only" → `"statusbar"`, "Both" → `"both"`

### Step 3: How often (welcome message)

Only ask this if the user chose "welcome" or "both" in Step 2. Use AskUserQuestion:

- **Every session (Recommended)** — description: "See the report each time you start Claude Code"
- **Once a day** — description: "Show once per day, skip if already shown in the last 24h"
- **Once a week** — description: "Show once per week — minimal interruption"

Map: "Every session" → `"session"`, "Once a day" → `"daily"`, "Once a week" → `"weekly"`

### Step 4: Vibe

Ask using AskUserQuestion with previews:

- **Keep it fun (Recommended)** — Preview:
  ```
  Includes real-world comparisons and
  a random fun fact each session:

    That's about:
      🍌 4.6 bananas grown
      🚿 3.7 minutes of hot shower

    💬 Caching is basically your AI
       carpooling. 83% of tokens
       hitched a ride this week.
  ```

- **Just the numbers** — Preview:
  ```
  Clean, minimal output.
  No comparisons, no fun facts.
  Just the stats you need.

    ⚡ Energy:    63.23 Wh
    🌍 CO2:       37.0g
    💰 Cost:      $902.47
  ```

Map: "Keep it fun" → `"fun"`, "Just the numbers" → `"minimal"`

### Step 5: Monthly budget (optional)

Ask using AskUserQuestion:

- **Yes, set a budget** — description: "Track monthly spending against a target. Shows a progress bar in the welcome message and budget usage in the status bar."
- **No thanks (Recommended)** — description: "Skip budget tracking"

If they choose yes, ask a follow-up: "What's your monthly budget in USD?" with options:
- **$50/month**
- **$100/month (Recommended)**
- **$200/month**
- (User can type a custom amount via "Other")

Map: dollar amount → `"monthly_budget": <number>`, or null if skipped.

### Step 6: Model efficiency goals (optional)

Ask using AskUserQuestion with previews:

- **Yes, track efficiency** — Preview:
  ```
  Model efficiency: B
    Haiku      ▓▓▓▓▓▓▓▓░░░░░░░░░░░░  42% (target >=20%) ✓
    Sonnet     ▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░  55% (target <=75%) ✓
    Opus       ▓░░░░░░░░░░░░░░░░░░░   3% (target <=5%)  ✓

  Grades: A = all met, B = 2/3, C = 1/3, D = 0/3
  ```

- **No thanks (Recommended)** — description: "Skip model efficiency grading"

If they choose yes, ask a follow-up: "What's your ideal model usage split? These are cost-based percentages — what % of your spending should go to each tier."

Use AskUserQuestion with previews:

- **Default (Haiku ≥70%, Sonnet ≤25%, Opus ≤5%)** — Preview:
  ```
  Optimized for cost efficiency.
  Pushes you toward cheaper models.

    Haiku   ≥70%  (most usage)
    Sonnet  ≤25%  (some usage)
    Opus    ≤5%   (rare usage)
  ```

- **Balanced (Haiku ≥20%, Sonnet ≤75%, Opus ≤5%)** — Preview:
  ```
  Realistic for most developers.
  Sonnet for daily work, Haiku for
  sub-agents, Opus sparingly.

    Haiku   ≥20%  (sub-agents + light tasks)
    Sonnet  ≤75%  (main workhorse)
    Opus    ≤5%   (complex reasoning only)
  ```

- **Power user (Haiku ≥10%, Sonnet ≤40%, Opus ≤50%)** — Preview:
  ```
  Heavy Opus usage for complex work.
  Higher cost but maximum capability.

    Haiku   ≥10%  (sub-agents only)
    Sonnet  ≤40%  (standard tasks)
    Opus    ≤50%  (primary model)
  ```

- (User can type custom targets via "Other", e.g. "Haiku 20%, Sonnet 75%, Opus 5%")

Map the selected profile to the corresponding thresholds in `efficiency_targets`.

### Step 7: Install

After collecting all answers:

1. Write the config to `~/.claude/co2-tracker-config.json`:
   ```json
   {
     "show": "<co2|cost|both>",
     "display": "<welcome|statusbar|both>",
     "frequency": "<session|daily|weekly>",
     "vibe": "<fun|minimal>",
     "monthly_budget": <number or null>,
     "efficiency_targets": <object or null>
   }
   ```

2. Find the script path. The script lives alongside this SKILL.md at `scripts/co2-tracker.py`. To get the absolute path, run:
   ```bash
   find ~/.claude/skills -path "*/usage-tracking/scripts/co2-tracker.py" 2>/dev/null | head -1
   ```
   Store this path — you'll use it in the hook commands. Do NOT copy the script to `~/.claude/` — it already lives in the plugin directory.

3. Read the user's `~/.claude/settings.json` and add the hooks. Be careful to merge, not overwrite existing settings. Use the absolute script path from step 2.

   Always add the Stop hook (for session-level status bar tracking):
   ```json
   {
     "hooks": {
       "Stop": [
         {
           "hooks": [
             {
               "type": "command",
               "command": "python3 /absolute/path/to/co2-tracker.py --stop-hook",
               "timeout": 5
             }
           ]
         }
       ]
     }
   }
   ```

   If display is "welcome" or "both", also add the SessionStart hook:
   ```json
   {
     "hooks": {
       "SessionStart": [
         {
           "hooks": [
             {
               "type": "command",
               "command": "python3 /absolute/path/to/co2-tracker.py",
               "timeout": 15
             }
           ]
         }
       ]
     }
   }
   ```

   If display is "statusbar" or "both", add:
   ```json
   {
     "statusLine": {
       "type": "command",
       "command": "python3 /absolute/path/to/co2-tracker.py --status-line"
     }
   }
   ```

4. Run a quick test to show the user their configured output:
   ```bash
   python3 /absolute/path/to/co2-tracker.py
   ```
   Parse the JSON output and show the `systemMessage` to the user.

5. Confirm setup is complete. Tell the user:
   - "You're all set! The tracker will show at your next session start."
   - "The status bar will update with session stats after each response."
   - "Run `/usage-tracking` anytime to change your preferences."
