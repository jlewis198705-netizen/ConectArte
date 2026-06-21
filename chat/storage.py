from storages.backends.s3boto3 import S3Boto3Storage

class SupabasePublicStorage(S3Boto3Storage):
    def url(self, name):
        s3_url = super().url(name)
        return s3_url.replace(
            '.storage.supabase.co/storage/v1/s3/',
            '.supabase.co/storage/v1/object/public/'
        )
