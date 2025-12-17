from fastapi import APIRouter , HTTPException
from schemas.uidModel import uidmodel
from database.fetchdata import getemployee ,getproductionbyemployee , update_date_fin ,gettachebyid,ajouter_production
router = APIRouter(prefix="" , tags=["production"])
