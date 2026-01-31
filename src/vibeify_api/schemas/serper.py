from __future__ import annotations

from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field


class SerperLinkSnippet(BaseModel):
    text: str
    link: Optional[str] = None


class SerperPrice(BaseModel):
    amount: float
    currency: str


class SerperCountry(BaseModel):
    name: str
    iso_code_alpha2: Optional[str] = None


class SerperSize(BaseModel):
    width: int
    height: int


class SerperImageVariant(BaseModel):
    link: str
    size: SerperSize


class SerperSearchMetadata(BaseModel):
    id: str
    status: str
    json_endpoint: str
    created_at: str
    processed_at: str
    ebay_product_url: str
    raw_html_file: str
    total_time_taken: float


class SerperSearchParameters(BaseModel):
    engine: str
    product_id: str
    ebay_domain: str


class SerperBuyItNow(BaseModel):
    price: SerperPrice


class SerperBuyOptions(BaseModel):
    options: List[str]
    buy_it_now: Optional[SerperBuyItNow] = None


class SerperShippingDates(BaseModel):
    snippets: List[SerperLinkSnippet]


class SerperShippingOption(BaseModel):
    via: str
    free: Optional[bool] = None
    dates: Optional[SerperShippingDates] = None


class SerperShippingTo(BaseModel):
    country: SerperCountry
    zip_code: str


class SerperShipping(BaseModel):
    from_: str = Field(alias="from")
    to: SerperShippingTo
    status: str
    options: List[SerperShippingOption]
    ships_to: Optional[Dict[str, List[SerperLinkSnippet]]] = None
    includes_countries: Optional[List[SerperCountry]] = None
    excludes_countries: Optional[List[SerperCountry]] = None
    handling_time: Optional[Dict[str, List[SerperLinkSnippet]]] = None
    taxes: Optional[Dict[str, List[SerperLinkSnippet]]] = None


class SerperReturnBlock(BaseModel):
    title: str
    snippets: List[SerperLinkSnippet]


class SerperPaymentMethod(BaseModel):
    title: str


class SerperFinancingOption(BaseModel):
    title: str
    snippet_groups: List[List[SerperLinkSnippet]]


class SerperPaymentMethods(BaseModel):
    payments: List[SerperPaymentMethod]
    financing: Optional[List[SerperFinancingOption]] = None


class SerperMediaItem(BaseModel):
    type: Literal["image"]
    image: List[SerperImageVariant]


class SerperSpecField(BaseModel):
    type: str
    title: str
    value: str


class SerperSpecSection(BaseModel):
    type: str
    fields: List[SerperSpecField]


class SerperSpecGroup(BaseModel):
    type: str
    title: str
    sections: List[SerperSpecSection]


class SerperRevisionDate(BaseModel):
    original: str
    iso8601: str


class SerperSpecifications(BaseModel):
    groups: List[SerperSpecGroup]
    last_revision_datetime: Optional[SerperRevisionDate] = None
    revisions_link: Optional[str] = None


class SerperCategory(BaseModel):
    title: str
    link: str


class SerperBuyerLimit(BaseModel):
    min: int
    max: int


class SerperQuantity(BaseModel):
    availability_signal: str
    available_per_buyer: SerperBuyerLimit
    sold: int


class SerperAdditionalService(BaseModel):
    id: str
    type: str
    title: str
    price: SerperPrice
    snippets: List[SerperLinkSnippet]


class SerperConfidenceItem(BaseModel):
    type: str
    title: str
    snippet_groups: List[List[SerperLinkSnippet]]


class SerperProductResults(BaseModel):
    product_id: str
    product_link: str
    title: str
    subtitle: Optional[str] = None
    short_description: Optional[str] = None
    full_description_link: Optional[str] = None
    watch_count: Optional[int] = None
    banner_status: Optional[str] = None
    buy: Optional[SerperBuyOptions] = None
    shipping: Optional[SerperShipping] = None
    returns: Optional[List[List[SerperReturnBlock]]] = None
    payment_methods: Optional[SerperPaymentMethods] = None
    media: Optional[List[SerperMediaItem]] = None
    specifications: Optional[SerperSpecifications] = None
    categories: Optional[List[SerperCategory]] = None
    condition: Optional[str] = None
    quantity: Optional[SerperQuantity] = None
    additional_services: Optional[List[SerperAdditionalService]] = None
    shop_with_confidence: Optional[List[SerperConfidenceItem]] = None


class SerperSellerRatingScore(BaseModel):
    title: str
    value: float


class SerperReviewAuthor(BaseModel):
    username: str
    rating: Optional[int] = None


class SerperReviewProduct(BaseModel):
    id: Optional[str] = None
    link: Optional[str] = None
    title: Optional[str] = None


class SerperReview(BaseModel):
    review_id: str
    sentiment: str
    author: SerperReviewAuthor
    text: str
    created_time: str
    verified_purchase: Optional[bool] = None
    image_link: Optional[str] = None
    product: Optional[SerperReviewProduct] = None


class SerperReviewGroup(BaseModel):
    count: int
    list: List[SerperReview]


class SerperReviewGroups(BaseModel):
    this_product: Optional[SerperReviewGroup] = None
    all_products: Optional[SerperReviewGroup] = None


class SerperSellerReviews(BaseModel):
    groups: SerperReviewGroups
    see_all_link: Optional[str] = None


class SerperPopularCategory(BaseModel):
    title: str
    link: str
    category_id: str


class SerperPopularCategories(BaseModel):
    list: List[SerperPopularCategory]
    see_all_link: Optional[str] = None


class SerperSellerResults(BaseModel):
    type: str
    name: str
    username: str
    bio: Optional[str] = None
    joined_at: Optional[str] = None
    sold_count: Optional[int] = None
    rating: Optional[int] = None
    positive_feedback: Optional[float] = None
    profile_link: Optional[str] = None
    logo_link: Optional[str] = None
    popular_categories: Optional[SerperPopularCategories] = None
    rating_scores: Optional[List[SerperSellerRatingScore]] = None
    reviews: Optional[SerperSellerReviews] = None


class SerperRelatedProduct(BaseModel):
    product_id: str
    product_link: str
    title: str
    price: SerperPrice
    image_link: Optional[str] = None
    condition: Optional[str] = None
    extensions: Optional[List[str]] = None
    bold_extensions: Optional[List[str]] = None
    strikethrough_extensions: Optional[List[str]] = None
    detected_extensions: Optional[Dict[str, bool]] = None
    signals: Optional[List[str]] = None


class SerperEbayProductResponse(BaseModel):
    search_metadata: SerperSearchMetadata
    search_parameters: SerperSearchParameters
    product_results: SerperProductResults
    seller_results: SerperSellerResults
    related_products: Optional[List[SerperRelatedProduct]] = None
