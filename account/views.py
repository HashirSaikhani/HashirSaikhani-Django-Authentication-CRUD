from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from account.serializers import UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer, UserChangePasswordSerializer, SendPasswordResetEmailSerializer, UserPasswordResetSerializer, FileSerializer
from account.renderers import UserRenderer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from account.models import File, User
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from rest_framework.pagination import PageNumberPagination


# Generate Token Manually
def get_tokens_for_user(user):
  refresh = RefreshToken.for_user(user)
  return {
      'refresh': str(refresh),
      'access': str(refresh.access_token),
  }

class UserRegistrationView(APIView):
    renderer_classes = [UserRenderer]

    def post(self, request, format=None):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = get_tokens_for_user(user)
        return Response({'token': token, 'msg': 'Registration Successful'}, status=status.HTTP_201_CREATED)


class UserLoginView(APIView):
    renderer_classes = [UserRenderer]

    def post(self, request, format=None):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token = get_tokens_for_user(user)
        return Response({'token': token, 'msg': 'Login Success'}, status=status.HTTP_200_OK)



class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        user = request.user
        files = request.FILES.getlist('file')
        if files:
            total_uploaded = File.objects.filter(user=user).count()
            remaining_slots = 20 - total_uploaded

            if len(files) > remaining_slots:
                return Response(
                    {'error': f'You can only upload a maximum of {remaining_slots} more files.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            for file in files:
                File.objects.create(file=file, name=file.name, user=user)

            return Response({'message': 'Files uploaded successfully.'}, status=status.HTTP_201_CREATED)
        return Response({'error': 'No files uploaded.'}, status=status.HTTP_400_BAD_REQUEST)



class FileListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        user = request.user
        files = File.objects.filter(user=user)
        
        paginator = PageNumberPagination()
        paginator.page_size = 15 
        
        result_page = paginator.paginate_queryset(files, request)
        serializer = FileSerializer(result_page, many=True)
      
        return paginator.get_paginated_response(serializer.data)




class FileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id, format=None):
        file_instance = get_object_or_404(File, id=file_id, user=request.user)

        file_path = file_instance.file.path
        if not default_storage.exists(file_path):
            raise Http404("File does not exist")

        with open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type=self.get_content_type(file_instance.name))
            response['Content-Disposition'] = f'attachment; filename="{file_instance.name}"'
            return response

    def get_content_type(self, filename):
        import mimetypes
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'




class FileDelete(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, file_id, format=None):
        file_instance = get_object_or_404(File, id=file_id, user=request.user)
        file_instance.file.delete(save=False)
        file_instance.delete()
        return Response({'message': 'File deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
    


class FileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, file_id, format=None):
        user = request.user
        file_instance = get_object_or_404(File, id=file_id, user=user)
        serializer = FileSerializer(file_instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class UserProfileView(APIView):
  renderer_classes = [UserRenderer]
  permission_classes = [IsAuthenticated]
  def get(self, request, format=None):
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)

class UserChangePasswordView(APIView):
  renderer_classes = [UserRenderer]
  permission_classes = [IsAuthenticated]
  def post(self, request, format=None):
    serializer = UserChangePasswordSerializer(data=request.data, context={'user':request.user})
    serializer.is_valid(raise_exception=True)
    return Response({'msg':'Password Changed Successfully'}, status=status.HTTP_200_OK)

class SendPasswordResetEmailView(APIView):
  renderer_classes = [UserRenderer]
  def post(self, request, format=None):
    serializer = SendPasswordResetEmailSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response({'msg':'Password Reset link send. Please check your Email'}, status=status.HTTP_200_OK)

class UserPasswordResetView(APIView):
  renderer_classes = [UserRenderer]
  def post(self, request, uid, token, format=None):
    serializer = UserPasswordResetSerializer(data=request.data, context={'uid':uid, 'token':token})
    serializer.is_valid(raise_exception=True)
    return Response({'msg':'Password Reset Successfully'}, status=status.HTTP_200_OK)

