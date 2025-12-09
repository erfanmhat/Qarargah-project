from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from core.models import Soldier, Leave
from core.api.serializers import (
    SoldierSerializer, LeaveSerializer, DashboardStatsSerializer
)


class SoldierViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing soldiers
    """
    queryset = Soldier.objects.select_related('service_status', 'current_location', 'health_status').prefetch_related('reductions')
    serializer_class = SoldierSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search filter
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(national_code__icontains=search) |
                Q(dossier_code__icontains=search)
            )
        
        # Dispatch type filter
        dispatch_type = self.request.query_params.get('dispatch_type', None)
        if dispatch_type:
            queryset = queryset.filter(dispatch_type=dispatch_type)
        
        # Service status filter
        service_status = self.request.query_params.get('service_status', None)
        if service_status:
            queryset = queryset.filter(service_status_id=service_status)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get soldier statistics"""
        total = self.get_queryset().count()
        active = self.get_queryset().filter(service_status__is_active_service=True).count()
        ending_soon = 0
        
        today = timezone.now().date()
        ninety_days_later = today + timedelta(days=90)
        
        for soldier in self.get_queryset():
            try:
                end_date = soldier.service_end_date()
                if end_date and today <= end_date <= ninety_days_later:
                    ending_soon += 1
            except:
                continue
        
        return Response({
            'total': total,
            'active': active,
            'ending_soon': ending_soon
        })


class LeaveViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing leaves
    """
    queryset = Leave.objects.select_related('soldier').all()
    serializer_class = LeaveSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search filter
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(soldier__first_name__icontains=search) |
                Q(soldier__last_name__icontains=search) |
                Q(soldier__national_code__icontains=search)
            )
        
        # Leave type filter
        leave_type = self.request.query_params.get('leave_type', None)
        if leave_type:
            queryset = queryset.filter(leave_type=leave_type)
        
        # Approval status filter
        is_approved = self.request.query_params.get('is_approved', None)
        if is_approved is not None:
            queryset = queryset.filter(is_approved=is_approved.lower() == 'true')
        
        # Date range filter
        start_date = self.request.query_params.get('start_date', None)
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        
        end_date = self.request.query_params.get('end_date', None)
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get leave statistics"""
        total = self.get_queryset().count()
        approved = self.get_queryset().filter(is_approved=True).count()
        pending = self.get_queryset().filter(is_approved=False).count()
        
        today = timezone.now().date()
        on_leave_today = self.get_queryset().filter(
            start_date__lte=today,
            end_date__gte=today,
            is_approved=True
        ).count()
        
        # Leave type distribution
        leave_types = self.get_queryset().values('leave_type').annotate(
            count=Count('id')
        )
        
        return Response({
            'total': total,
            'approved': approved,
            'pending': pending,
            'on_leave_today': on_leave_today,
            'by_type': list(leave_types)
        })


class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for dashboard statistics
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get dashboard statistics"""
        today = timezone.now().date()
        ninety_days_later = today + timedelta(days=90)
        
        total_soldiers = Soldier.objects.count()
        on_leave_today = Leave.objects.filter(
            start_date__lte=today,
            end_date__gte=today,
            is_approved=True
        ).count()
        
        # Calculate ending soon
        ending_soon = 0
        soldiers = list(Soldier.objects.select_related('service_status').prefetch_related('reductions').all())
        for soldier in soldiers:
            try:
                end_date = soldier.service_end_date()
                if end_date and today <= end_date <= ninety_days_later:
                    ending_soon += 1
            except:
                continue
        
        serializer = DashboardStatsSerializer({
            'total_soldiers': total_soldiers,
            'on_leave_today': on_leave_today,
            'ending_soon': ending_soon
        })
        
        return Response(serializer.data)

