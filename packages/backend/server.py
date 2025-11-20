import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

# package-relative import
from .schema import schema

app = FastAPI(title="Book Agent Backend")
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

@app.get("/")
async def root():
    return {"ok": True, "graphql": "/graphql"}
