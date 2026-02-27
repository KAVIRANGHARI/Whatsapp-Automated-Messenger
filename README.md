#WhatsApp-Automated-Messenger
A native desktop automation tool built using computer vision and template matching. This was my first major project as a CS student, a one-month deep dive into making a PC "see" and interact with software just like a human would.

Project Overview:
This repository contains a legacy project that automates the WhatsApp Desktop application. Unlike modern web-based scrapers that interact with HTML elements, this tool is entirely native. It uses template matching to identify UI elements from screenshots and simulates physical mouse clicks to navigate.

How To Use:


How It Works:
Initialization: The script launches the WhatsApp Desktop app and brings it to the foreground.

Template Matching: The system takes a real-time screenshot of your display. It then scans that image for a specific "template" (like a button or a text field). If a match is found, it calculates the exact (x,y) coordinates.

Interaction: Using Python libraries, the script moves the hardware cursor to those coordinates and executes a click.

Looping: These stages repeat based on the logic you define, allowing for complex, multi-step messaging and/or forwarding.

Why Template Matching?
Note: While modern automation often uses Chrome DevTools or APIs, I chose this "primal" method because it was the most accessible way for me to solve the problem at the time. It treats the screen as a canvas rather than a data structure.

I personally used this tool within a Virtual Machine (VM) to:

Run mass messaging for community updates in the background.

Bypass the logistical limits of standard groups or broadcasts.

Keep my main OS free for other work while the "bot" operated in its own isolated environment.

Ethics & FOSS:
I am a firm believer in Free and Open Source Software (FOSS) and the idea that users should have the agency to use software as they see fit. However, with great power comes the responsibility to avoid malicious practices.

Please use this tool ethically. I developed this for community management.

Reflection:
This project was my first real "sprint." It took about a week to build a working prototype and another three weeks to refine the logic. While I used AI assistance to troubleshoot, the core architecture and logic flow are original.

It marks the beginning of my journey as a developer. I’m now moving on to bigger, more optimized systems, but this "rookie" project will always be the foundation of my growth as a CS student.
