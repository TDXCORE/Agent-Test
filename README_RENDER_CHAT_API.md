# Deploying the Chat API to Render

This document explains how to deploy the FastAPI Chat API to Render.

## Overview

The Chat API is a FastAPI application that provides endpoints for managing conversations, messages, and users. It uses Supabase as the database backend.

## Deployment Steps

1. **Push your code to a Git repository**

   Make sure your code is pushed to a Git repository (GitHub, GitLab, etc.) that Render can access.

2. **Create a new Web Service on Render**

   - Log in to your Render account
   - Click on "New" and select "Web Service"
   - Connect your Git repository
   - Configure the service:
     - Name: `chat-api` (or your preferred name)
     - Environment: `Python`
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `cd endpoint && uvicorn api:app --host=0.0.0.0 --port=$PORT`

3. **Set Environment Variables**

   In the Render dashboard, add the following environment variables:
   
   - `NEXT_PUBLIC_SUPABASE_URL`: Your Supabase URL
   - `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key

4. **Deploy the Service**

   Click "Create Web Service" to deploy your application.

## Using the Blueprint Specification

Alternatively, you can use the `render.yaml` file in this repository to deploy both the WhatsApp webhook and the Chat API services at once:

1. Fork this repository to your own GitHub account
2. In the Render dashboard, click on "New" and select "Blueprint"
3. Connect your forked repository
4. Render will automatically detect the `render.yaml` file and create both services

## API Documentation

Once deployed, you can access the API documentation at:

- Swagger UI: `https://your-service-name.onrender.com/docs`
- ReDoc: `https://your-service-name.onrender.com/redoc`

## Endpoints

The API provides the following endpoints:

### Conversations

- `GET /api/conversations?user_id={user_id}` - Get all active conversations for a specific user
- `POST /api/conversations` - Create a new conversation

### Messages

- `GET /api/messages?conversation_id={conversation_id}` - Get all messages for a specific conversation
- `POST /api/messages` - Create a new message

### Users

- `GET /api/users` - Get all users with transformed data for frontend
