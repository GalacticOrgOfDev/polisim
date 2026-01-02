# GitHub Discussions Setup Guide

**Purpose:** Copy-paste content for setting up GitHub Discussions categories on the PoliSim repository.

---

## How to Enable Discussions

1. Go to: `https://github.com/GalacticOrgOfDev/polisim/settings`
2. Scroll to "Features" section
3. Check ✅ "Discussions"
4. Click "Set up discussions"

---

## Discussion Categories to Create

After enabling, go to: `https://github.com/GalacticOrgOfDev/polisim/discussions/categories`

Click "New category" for each of the following:

---

### Category 1: 📣 Announcements

**Settings:**
- **Emoji:** 📣
- **Category name:** Announcements
- **Description:** (copy below)
- **Discussion Format:** Announcement
- **Permissions:** Only maintainers can post

**Description to copy:**
```
Official announcements from the PoliSim team. New releases, breaking changes, roadmap updates, and project news.
```

---

### Category 2: 💬 General

**Settings:**
- **Emoji:** 💬
- **Category name:** General
- **Description:** (copy below)
- **Discussion Format:** Open-ended discussion
- **Permissions:** Everyone can post

**Description to copy:**
```
General discussion about PoliSim, fiscal policy simulation, and related topics. A place for the community to connect and chat.
```

---

### Category 3: 💡 Ideas & Feature Requests

**Settings:**
- **Emoji:** 💡
- **Category name:** Ideas & Feature Requests
- **Description:** (copy below)
- **Discussion Format:** Open-ended discussion
- **Permissions:** Everyone can post

**Description to copy:**
```
Share your ideas for new features, policy domains, or improvements to PoliSim. Discuss potential enhancements before they become formal issues.
```

---

### Category 4: 🙋 Q&A / Help

**Settings:**
- **Emoji:** 🙋
- **Category name:** Q&A / Help
- **Description:** (copy below)
- **Discussion Format:** Question / Answer
- **Permissions:** Everyone can post

**Description to copy:**
```
Ask questions about using PoliSim, interpreting results, configuring simulations, or API usage. Community members and maintainers will help answer.
```

---

### Category 5: 🎓 Learning & Tutorials

**Settings:**
- **Emoji:** 🎓
- **Category name:** Learning & Tutorials
- **Description:** (copy below)
- **Discussion Format:** Open-ended discussion
- **Permissions:** Everyone can post

**Description to copy:**
```
Educational content, tutorials, Jupyter notebooks, and resources for learning about fiscal policy simulation. Share your teaching materials or ask for learning resources.
```

---

### Category 6: 🔬 Research & Academia

**Settings:**
- **Emoji:** 🔬
- **Category name:** Research & Academia
- **Description:** (copy below)
- **Discussion Format:** Open-ended discussion
- **Permissions:** Everyone can post

**Description to copy:**
```
Academic research using PoliSim, methodology discussions, validation studies, and scholarly collaboration. Connect with researchers and share findings.
```

---

### Category 7: 🏆 Show and Tell

**Settings:**
- **Emoji:** 🏆
- **Category name:** Show and Tell
- **Description:** (copy below)
- **Discussion Format:** Open-ended discussion
- **Permissions:** Everyone can post

**Description to copy:**
```
Show off what you've built with PoliSim! Share your policy analyses, visualizations, integrations, or creative uses of the simulation engine.
```

---

### Category 8: 🗳️ Polls

**Settings:**
- **Emoji:** 🗳️
- **Category name:** Polls
- **Description:** (copy below)
- **Discussion Format:** Poll
- **Permissions:** Only maintainers can post

**Description to copy:**
```
Community polls for gathering feedback on project direction, feature prioritization, and decision-making.
```

---

## Welcome Discussion Post

After creating categories, create a welcome post in **📣 Announcements**:

**Title:** Welcome to PoliSim Discussions! 🎉

**Body to copy:**

```markdown
# Welcome to PoliSim Discussions! 🎉

We're excited to launch the PoliSim community discussion space! This is your place to connect with other users, researchers, developers, and policymakers interested in fiscal policy simulation.

## 🗂️ How to Use Discussions

| Category | Purpose |
|----------|---------|
| 📣 **Announcements** | Official news, releases, and project updates |
| 💬 **General** | Chat about PoliSim and fiscal policy |
| 💡 **Ideas & Feature Requests** | Suggest and discuss new features |
| 🙋 **Q&A / Help** | Get help with using PoliSim |
| 🎓 **Learning & Tutorials** | Educational content and resources |
| 🔬 **Research & Academia** | Academic collaboration and research |
| 🏆 **Show and Tell** | Share what you've built |
| 🗳️ **Polls** | Community feedback polls |

## 📜 Community Guidelines

Please read our [Code of Conduct](https://github.com/GalacticOrgOfDev/polisim/blob/main/CODE_OF_CONDUCT.md) before participating. We're building a welcoming, inclusive community focused on advancing policy analysis tools.

## 🚀 Getting Started

- **New to PoliSim?** Check out our [README](https://github.com/GalacticOrgOfDev/polisim#readme) and [FAQ](https://github.com/GalacticOrgOfDev/polisim/blob/main/FAQ.md)
- **Want to contribute?** Read our [Contributing Guide](https://github.com/GalacticOrgOfDev/polisim/blob/main/CONTRIBUTING.md)
- **Have questions?** Post in [Q&A / Help](../categories/q-a-help)
- **Have an idea?** Share it in [Ideas & Feature Requests](../categories/ideas-feature-requests)

## 👋 Introduce Yourself!

Feel free to reply to this discussion and introduce yourself:
- What's your background?
- What interests you about policy simulation?
- What would you like to see in PoliSim?

We're thrilled to have you here! 🚀
```

---

## Additional Setup Tasks

### Pin the Welcome Post
After creating the welcome discussion, click the `...` menu and select "Pin discussion"

### Set Up Category Permissions
For each category, verify:
- 📣 Announcements: Only maintainers can create new discussions
- 🗳️ Polls: Only maintainers can create new discussions
- All others: Everyone can post

### Link Discussions in Repository
Update README.md to include:
```markdown
## Community

Join the discussion! [GitHub Discussions](https://github.com/GalacticOrgOfDev/polisim/discussions)
```

---

## Checklist

- [ ] Enable Discussions in repository settings
- [ ] Create 📣 Announcements category
- [ ] Create 💬 General category
- [ ] Create 💡 Ideas & Feature Requests category
- [ ] Create 🙋 Q&A / Help category
- [ ] Create 🎓 Learning & Tutorials category
- [ ] Create 🔬 Research & Academia category
- [ ] Create 🏆 Show and Tell category
- [ ] Create 🗳️ Polls category
- [ ] Post welcome discussion
- [ ] Pin welcome discussion
- [ ] Update README with Discussions link
- [ ] Delete default categories if any (General, Ideas, etc. that GitHub creates automatically)

---

*This document was created as part of PoliSim Phase 6.4: Community Infrastructure*
