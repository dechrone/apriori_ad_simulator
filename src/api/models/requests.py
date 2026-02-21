"""API request models."""

from typing import List, Literal, Optional
from pydantic import BaseModel, EmailStr, Field, HttpUrl, model_validator


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    display_name: Optional[str] = None
    company_name: Optional[str] = None
    role: Optional[str] = None


class RunSimulationRequest(BaseModel):
    """
    Request body for POST /api/v1/simulations/run.

    simulation_type:
        0 = Ad simulation   (each URL is an ad creative image)
        1 = Product flow    (each URL is a screen in the flow, ordered)

    target_group: free-text description of the user segment to simulate,
        e.g. "young urban freelancers aged 22-30 in Tier-2 Indian cities"

    image_urls: publicly accessible URLs of the images to be downloaded (optional if local_ads_dir is set).
    local_ads_dir: if provided and image_urls is empty, use images from this folder (relative to backend root or absolute).
    """

    n: int = Field(ge=1, le=100, description="Number of personas to simulate")
    target_group: str = Field(
        min_length=3,
        description="Free-text user segment description (e.g. 'urban millennials in Bengaluru')",
    )
    simulation_type: Literal[0, 1] = Field(
        description="0 = Ad simulation, 1 = Product flow simulation"
    )
    image_urls: Optional[List[HttpUrl]] = Field(
        default=None,
        description="Ordered list of image URLs to download; omit if using local_ads_dir",
    )
    local_ads_dir: Optional[str] = Field(
        default=None,
        description="Use images from this folder when image_urls is not provided (e.g. 'ads_ohsou')",
    )
    product_category: Optional[str] = Field(
        default="general",
        description="Product category context, e.g. 'fintech', 'd2c_fashion', 'healthcare'",
    )

    @model_validator(mode="after")
    def require_images_or_local_dir(self):
        if (not self.image_urls or len(self.image_urls) == 0) and not self.local_ads_dir:
            raise ValueError("Either image_urls (non-empty) or local_ads_dir must be provided.")
        return self


# ---------------------------------------------------------------------------
# Frontend contract: product-flow and ad-portfolio (Clerk + Firestore)
# ---------------------------------------------------------------------------

class ProductFlowSimulationRequest(BaseModel):
    """POST /api/v1/simulations/product-flow – matches frontend API docs."""
    profileId: str = Field(description="Clerk user id; matches clerkId in apriori_users to identify user profile")
    name: str = Field(description="Simulation name from the form")
    audience: str = Field(description="Selected audience id (e.g. us-smb-founders); used to get audience description from Firestore")
    personaDepth: Literal["low", "medium", "high"] = Field(description="Persona depth; we use n=1 in all cases")
    optimizeMetric: str = Field(description="Metric to optimize for (e.g. signup-completion, activation, checkout-conversion)")
    selectedFolderIds: List[str] = Field(description="Asset folder ids chosen for the simulation")


class AdPortfolioSimulationRequest(BaseModel):
    """POST /api/v1/simulations/ad-portfolio – matches frontend API docs."""
    profileId: str = Field(description="Clerk user id; matches clerkId in apriori_users")
    name: str = Field(description="Simulation name from the form")
    audience: str = Field(description="Selected audience id")
    selectedFolderId: str = Field(description="Single ad-creative folder id")
