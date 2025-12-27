# Quick Start: Workflow Playground

## 🚀 Get Started in 30 Seconds

### 1. Open the Playground
Click the **P** icon in the left sidebar of TerraQore Studio

### 2. Enter a Workflow Prompt
Type what you want the agents to do:
```
"Analyze the top 5 Python web frameworks and compare them"
```

### 3. Execute
Click the **▶ Execute Workflow** button

### 4. Monitor Execution
- Watch steps appear in real-time
- Statistics update automatically
- See agent communications in the log

### 5. Inspect Results
Click any step to view its detailed output

## 📊 Understanding the Interface

### Left Panel (Workflow Visualization)
```
┌─ Prompt Input (textarea)
├─ Execute Button
├─ Statistics (5 cards)
└─ Workflow Steps (scrollable list)
```

### Right Panel (Details & Logs)
```
┌─ Selected Step Details
│  ├─ Status & Type
│  ├─ Output Display
│  └─ Metadata
└─ Activity Log (last 10 entries)
```

## 🎯 Example Workflows

### Data Analysis
```
Analyze Q4 sales data from the provided CSV and generate 
insights about regional performance and product trends
```

### Code Generation
```
Create a Python function that validates email addresses 
and handles common edge cases. Include unit tests.
```

### Research Task
```
Research the top 3 competitors in the project management 
software space and create a comparison matrix
```

### Content Creation
```
Write a 500-word blog post about the benefits of 
microservices architecture in modern applications
```

## 📈 Monitoring Tips

| What to Look For | What It Means |
|------------------|---------------|
| Green ✓ steps | Successfully completed tasks |
| Blue ⚙ steps (pulsing) | Currently executing |
| Red ✕ steps | Failed - check output for errors |
| Gray ○ steps | Waiting to execute |

## 🔍 How to Debug

1. **Step fails?** → Click it to see the error message
2. **Unexpected output?** → Review the activity log
3. **Slow execution?** → Check running steps in statistics
4. **Want more details?** → Click on completed steps

## ⌨️ Keyboard Tips

- **Ctrl+Enter** in the prompt area = Submit workflow
- **Scroll** anywhere to navigate
- **Click** any step to inspect

## 🎨 Color Guide

- 🟢 **Green** = Complete ✓
- 🔵 **Blue** = Executing ⚙
- 🔴 **Red** = Failed ✕
- ⚪ **Gray** = Idle ○

## 💡 Pro Tips

1. **Be specific** in your prompts (helps agents understand)
2. **Include context** (e.g., "for a B2B SaaS company")
3. **Request format** (e.g., "as JSON", "as markdown table")
4. **Set expectations** (e.g., "in 300 words", "3 items")

Example:
```
NOT: "Generate a report"
YES: "Generate a 500-word market analysis report for 
      the enterprise software market as a markdown document"
```

## 🛠️ Troubleshooting

### Workflow won't start
- Check that your prompt isn't empty
- Ensure the server is running

### No results shown
- Step may still be executing (wait a moment)
- Check the activity log for errors

### Performance lag
- Try a simpler prompt first
- Very complex workflows take longer to execute

## 📚 Learn More

- [Full Playground Guide](PLAYGROUND_GUIDE.md) - Comprehensive documentation
- [Main README](README.md) - Architecture and setup
- [Implementation Details](IMPLEMENTATION_SUMMARY.md) - Technical overview

---

**Ready to try it? Open TerraQore Studio and click the P icon!** 🎮
