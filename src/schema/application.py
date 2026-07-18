from pydantic import BaseModel, Field


class Service(BaseModel):
    image: str = Field(description="Image uri")
    name: str = Field(description="Name")


class Application(BaseModel):
    name: str = Field(description="Name")
    services: list[Service] = Field(..., description="List of services", min_length=1)
