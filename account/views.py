from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from account.serializers import UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer, UserChangePasswordSerializer, SendPasswordResetEmailSerializer, UserPasswordResetSerializer, FileListSerializer
from account.renderers import UserRenderer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from account.models import File, User
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from rest_framework.pagination import PageNumberPagination
import logging, os

# Function to generate JWT tokens for the user
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class UserRegistrationView(APIView):
    renderer_classes = [UserRenderer]

    # Handle user registration
    def post(self, request, format=None):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = get_tokens_for_user(user)
        return Response({'token': token, 'msg': 'Registration Successful'}, status=status.HTTP_201_CREATED)

class UserLoginView(APIView):
    renderer_classes = [UserRenderer]

    # Handle user login
    def post(self, request, format=None):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token = get_tokens_for_user(user)
        return Response({'token': token, 'msg': 'Login Success'}, status=status.HTTP_200_OK)

class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]

    # Handle file upload
    def post(self, request, format=None):
        user = request.user
        files = request.FILES.getlist('file')
        if files:
            total_uploaded = user.no_of_files_uploaded
            remaining_slots = 20 - total_uploaded

            if len(files) > remaining_slots:
                return Response(
                    {'error': f'You can only upload a maximum of {remaining_slots} more files.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            for file in files:
                File.objects.create(file=file, name=file.name, user=user)

            # Update the count of files uploaded by the user
            user.no_of_files_uploaded += len(files)
            user.save()

            return Response({'message': 'Files uploaded successfully.'}, status=status.HTTP_201_CREATED)
        return Response({'error': 'No files uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class FileListPagination(PageNumberPagination):
    page_size = 15

class FileListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = FileListPagination

    # List files with pagination
    def get(self, request, format=None):
        user = request.user
        files = File.objects.filter(user=user)
        
        paginator = FileListPagination()
        result_page = paginator.paginate_queryset(files, request)

        logging.debug(f"Page number: {request.query_params.get('page', '1')}")
        logging.debug(f"Number of files retrieved: {len(result_page)}")

        serializer = FileListSerializer(result_page, many=True)
      
        return paginator.get_paginated_response(serializer.data)

class FileView(APIView):
    permission_classes = [IsAuthenticated]

    # View a file by its ID
    def get(self, request, file_id, format=None):
        file_instance = get_object_or_404(File, id=file_id, user=request.user)

        file_path = file_instance.file.path
        if not default_storage.exists(file_path):
            raise Http404("File does not exist")

        with open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type=self.get_content_type(file_instance.name))
            response['Content-Disposition'] = f'attachment; filename="{file_instance.name}"'
            return response

    # Determine the content type of a file
    def get_content_type(self, filename):
        import mimetypes
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'

class FileDelete(APIView):
    permission_classes = [IsAuthenticated]

    # Delete a file and update the user's file count
    def delete(self, request, file_id, format=None):
        file_instance = get_object_or_404(File, id=file_id, user=request.user)
        user = request.user

        # Delete the file from storage
        file_instance.file.delete(save=False)
        
        # Delete the file instance
        file_instance.delete()

        # Decrement the user's file count and save the user instance
        user.no_of_files_uploaded = max(0, user.no_of_files_uploaded - 1)
        user.save()

        return Response({'message': 'File deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

class FileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    # Update file details or content
    def put(self, request, file_id, format=None):
        user = request.user
        file_instance = get_object_or_404(File, id=file_id, user=user)
        
        # Extract data from the request
        new_name = request.data.get('name', file_instance.name)
        new_file = request.FILES.get('file', None)

        # Handle file renaming
        if new_name and new_name != file_instance.name:
            old_file_path = file_instance.file.path
            new_file_path = os.path.join(os.path.dirname(old_file_path), new_name)
            
            # Rename the file in the filesystem
            os.rename(old_file_path, new_file_path)
            
            # Update the file path in the model
            file_instance.file.name = os.path.join(os.path.dirname(file_instance.file.name), new_name)
            file_instance.name = new_name

        # Update the file if provided
        if new_file:
            file_instance.file.delete(save=False)  # Delete the old file from storage
            file_instance.file.save(new_file.name, new_file)

        # Save the changes
        file_instance.save()
        
        # Serialize the updated file instance
        serializer = FileListSerializer(file_instance)

        return Response(serializer.data, status=status.HTTP_200_OK)

class UserProfileView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    # Retrieve user profile information
    def get(self, request, format=None):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserChangePasswordView(APIView):
    renderer_classes = [UserRenderer]
    permission_classes = [IsAuthenticated]

    # Change user password
    def post(self, request, format=None):
        serializer = UserChangePasswordSerializer(data=request.data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)
        return Response({'msg': 'Password Changed Successfully'}, status=status.HTTP_200_OK)

class SendPasswordResetEmailView(APIView):
    renderer_classes = [UserRenderer]

    # Send password reset email
    def post(self, request, format=None):
        serializer = SendPasswordResetEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'msg': 'Password Reset link sent. Please check your Email'}, status=status.HTTP_200_OK)

class UserPasswordResetView(APIView):
    renderer_classes = [UserRenderer]

    # Reset user password
    def post(self, request, uid, token, format=None):
        serializer = UserPasswordResetSerializer(data=request.data, context={'uid': uid, 'token': token})
        serializer.is_valid(raise_exception=True)
        return Response({'msg': 'Password Reset Successfully'}, status=status.HTTP_200_OK)
