from fastapi import APIRouter
from requests import api

from app.api.routes import items, login, login_debug, private, users, utils, unified, unified_v2, sales_order_doc_d, feature, feature_d, material_class, material, surfaceTechnology, inventory, material_density, operation, nesting_layout, production_order, invoice, config, health, roles, permissions, companies, statistics
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(sales_order_doc_d.router)
api_router.include_router(feature.router)
api_router.include_router(feature_d.router)
api_router.include_router(material_class.router)
api_router.include_router(material.router)
api_router.include_router(material_density.router)
api_router.include_router(inventory.router)
api_router.include_router(surfaceTechnology.router)
api_router.include_router(operation.router)
api_router.include_router(nesting_layout.router)
api_router.include_router(production_order.router)
api_router.include_router(unified.router)
api_router.include_router(unified_v2.router)
api_router.include_router(invoice.router)
api_router.include_router(config.router)
api_router.include_router(health.router)
api_router.include_router(roles.router)
api_router.include_router(permissions.router)
api_router.include_router(companies.router)
api_router.include_router(statistics.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
    api_router.include_router(login_debug.router)
