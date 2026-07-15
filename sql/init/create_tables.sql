CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-----------------------------------------------------
-- USERS
-----------------------------------------------------

CREATE TABLE users (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    username VARCHAR(50) UNIQUE NOT NULL,

    email VARCHAR(255) UNIQUE NOT NULL,

    password_hash TEXT NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT NOW()

);

-----------------------------------------------------
-- CONVERSATIONS
-----------------------------------------------------

CREATE TABLE conversations (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    user_id UUID NOT NULL,

    title TEXT NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_user
        FOREIGN KEY(user_id)
        REFERENCES users(id)
        ON DELETE CASCADE

);

-----------------------------------------------------
-- MESSAGES
-----------------------------------------------------

CREATE TABLE messages (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    conversation_id UUID NOT NULL,

    role VARCHAR(20) NOT NULL,

    content TEXT NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_conversation
        FOREIGN KEY(conversation_id)
        REFERENCES conversations(id)
        ON DELETE CASCADE

);