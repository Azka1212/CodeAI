from django.urls import path
from .views import code_explainer, convert_code, detect_bugs, prompt_to_code, design_to_code, image_to_solve, solve_with_doc

urlpatterns = [
    path('api/convert_code/', convert_code, name='convert_code'),
    path('api/prompt_to_code/', prompt_to_code, name='prompt_to_code'),
    path('api/design_to_code/', design_to_code, name='design_to_code'),
    path('api/image_to_solve/', image_to_solve, name='image_to_solve'),
    path('api/solve_with_doc/', solve_with_doc, name='solve_with_doc'),
    path('api/code_explainer/', code_explainer, name='code_explainer'),
    path('api/detect_bugs/', detect_bugs, name='detect_bugs')

]
