from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from .serializers import RegisterSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status 
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import CustomTokenObtainPairSerializer
from .models import Profile
from decouple import config 

# Load env vars
PAT = config('PAT')
USER_ID = config('USER_ID')
APP_ID = config('APP_ID')
MODEL_ID = config('MODEL_ID')
MODEL_VERSION_ID = config('MODEL_VERSION_ID')
IMAGE_URL = config('IMAGE_URL')



User = get_user_model()

class SignInView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not check_password(password, user.password):
            return Response(
                {"error": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # ✅ Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "message": "Login successful",
            "entries": user.profile_user.entries
        }, status=status.HTTP_200_OK)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


class CustomTokenObtainPairView(APIView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = serializer.validated_data 
        response = Response(tokens, status=status.HTTP_200_OK)
        return response()

@api_view(["GET"])
@permission_classes([IsAuthenticated])   # user must be logged in
def profile_view(request):
    user = request.user
    return Response(
        {"user": user.profile_user.id},  # or serialize the profile
        status=status.HTTP_200_OK
    )

@api_view(["POST"])
def handle_image(request):
    user_id = request.data.get("id")
    if not user_id:
        return Response({"error": "User ID required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(id=user_id)
        profile = user.profile_user  # assuming you have a Profile model with `entries`
        profile.entries += 1
        profile.save()
        return Response({"entries": profile.entries}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])   # user must be logged in
def handle_api(request):

    image_url = request.data.get("image_url")
    if image_url is None:
        return Response({"error": "Image URL required"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get user's profile
    profile = Profile.objects.filter(user=request.user).first()
    
    if not profile:
        return Response(
            {"error": "User profile not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    

    


    headers = {
        "Authorization": f"Key {PAT}",
        "Content-Type": "application/json"
    }

    payload = {
        "user_app_id": {
            "user_id": USER_ID,
            "app_id": APP_ID
        },
        "inputs": [
            {
                "data": {
                    "image": {"url": image_url}
                }
            }
        ]
    }

    clarifai_url = f"https://api.clarifai.com/v2/models/{MODEL_ID}/versions/{MODEL_VERSION_ID}/outputs"
    

    try:
        r = requests.post(clarifai_url, headers=headers, json=payload)
        response_data = r.json()
        
        #  ONLY UPDATE IF CLARIFAI SUCCEEDS
        if r.status_code == 200:
            profile.entries += 1
            profile.save(update_fields=["entries"])
            
            # attach updated entries count
            response_data["entries"] = profile.entries
        else:
            response_data["entries"] = profile.entries


        return Response(response_data, status=r.status_code)
    
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


