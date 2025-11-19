1. 🌟 Project Overview
This project proposes an accessible web application, EchoMarket, designed to facilitate online grocery shopping specifically for visually impaired users.
The core aim is to remove barriers in e-commerce through intuitive, hands-free interaction utilizing voice commands and audio feedback.

2. 👨‍💻 Development Team
Betül Ulutürk - Backend Development, Core Functionality - betululuturk09@gmail.com
Arzu Irmak Findos - Database Design & Management - arzu.findos@gmail.com
Asya Ödül Koç - Frontend Development, Voice Integration - asyaodulkoc@gmail.com

3. ⚙️ System Architecture: Three-Tier Model
The application is structured using a Three-Tier Architecture to ensure separation of concerns, scalability, and maintainability.
Presentation Layer (Frontend): Manages all user interaction, voice input/output, and accessibility features (high-contrast design).

Business Logic Layer (Backend Services): Handles core features like product filtering based on voice commands, cart calculation, and order validation.

Data Access Layer (Database/APIs): Manages storage, retrieval, and synchronization of all product and user data.

4. 🛠️ Technological Stack (Tech Stack)
Frontend - HTML5, CSS3, JavaScript - Implementation of Web Speech API for Speech-to-Text (STT) and Text-to-Speech (TTS) integration.
Backend - Python, FastAPI - Provides high performance and ease of integration with NLP libraries.
Database - PostgreSQL - Used for reliable storage of users, products, carts, and orders.
Cloud/Deployment - Supabase - Managed Cloud Database solution for seamless remote access and collaboration.

5. 🚀 Core Functionality Scope (MVP Focus)
The core focus is on the complete transactional flow for groceries.

Voice-Guided Navigation: Hands-free interaction using voice commands (e.g., "filter by price", "add to cart")
Audio Feedback: Automatic audio description of products (name, price, rating) and audio confirmation of cart actions.
Transactional Flow: Complete cycle from Search -> Add to Cart -> Confirm Order will be functional.