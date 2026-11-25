from rest_framework import serializers

from .models import Doctor, Patient, Specialty


class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ('id', 'name')


class UserAccountSerializer(serializers.ModelSerializer):
    """Base commune à Doctor et Patient : gère le hachage du mot de passe
    et rend l'identifiant métier non modifiable après la création."""

    password = serializers.CharField(
        write_only=True,
        required=False,
        style={'input_type': 'password'},
    )
    business_id_field = None

    def get_fields(self):
        fields = super().get_fields()
        if isinstance(self.instance, (Doctor, Patient)):
            fields[self.business_id_field].read_only = True
        return fields

    def validate(self, attrs):
        if self.instance is None and not attrs.get('password'):
            raise serializers.ValidationError({'password': "Ce champ est obligatoire."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        many_to_many = self._pop_many_to_many(validated_data)
        user = self.Meta.model.objects.create_user(password=password, **validated_data)
        for name, values in many_to_many.items():
            getattr(user, name).set(values)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save(update_fields=['password'])
        return instance

    def _pop_many_to_many(self, validated_data):
        return {}


class DoctorSerializer(UserAccountSerializer):
    business_id_field = 'license_number'
    specialty_names = serializers.SlugRelatedField(
        source='specialties', many=True, read_only=True, slug_field='name'
    )

    class Meta:
        model = Doctor
        fields = (
            'id', 'username', 'password', 'first_name', 'last_name', 'email',
            'license_number', 'phone', 'specialties', 'specialty_names',
        )

    def _pop_many_to_many(self, validated_data):
        return {'specialties': validated_data.pop('specialties', [])}


class PatientSerializer(UserAccountSerializer):
    business_id_field = 'national_id'

    class Meta:
        model = Patient
        fields = (
            'id', 'username', 'password', 'first_name', 'last_name', 'email',
            'national_id', 'phone', 'birth_date',
        )
