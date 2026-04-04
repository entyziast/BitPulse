from fastapi import APIRouter


router = APIRouter(
    prefix='/tickers',
    tags=['tickers', ],
)


@router.get('/')
def test():
    return {'q': 123}