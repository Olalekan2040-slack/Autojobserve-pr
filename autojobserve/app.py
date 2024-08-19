import sys
sys.path.append('.')

from fastapi import FastAPI
from autojobserve.routers import user
from autojobserve.dummy_jobs import create_dummy_jobs
from fastapi.middleware.cors import CORSMiddleware
from autojobserve.auth import auth
app = FastAPI()

create_dummy_jobs()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
# app.include_router(user)
app.include_router(auth)