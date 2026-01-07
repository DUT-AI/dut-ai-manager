from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_examples():
    """Get all examples"""
    return {"message": "List of examples"}


@router.get("/{example_id}")
async def get_example(example_id: int):
    """Get a specific example by ID"""
    return {"example_id": example_id, "message": "Example details"}


@router.post("/")
async def create_example():
    """Create a new example"""
    return {"message": "Example created"}


@router.put("/{example_id}")
async def update_example(example_id: int):
    """Update an example"""
    return {"example_id": example_id, "message": "Example updated"}


@router.delete("/{example_id}")
async def delete_example(example_id: int):
    """Delete an example"""
    return {"example_id": example_id, "message": "Example deleted"}
