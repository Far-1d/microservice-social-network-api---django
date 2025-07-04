from . import version_aware_dispatch
from apps.relationships.api.v1_0.views.block import(
    BlockApi as v1_BlockApi,
)

# Create your views here.

BlockViews = version_aware_dispatch({
    '1.0': v1_BlockApi,
    '2.0': v1_BlockApi      
})