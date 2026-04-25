import React from 'react';
import { Bell, CheckCircle, AlertTriangle, Shield, Pill, Clock } from 'lucide-react';


const notifications = [
  {
    id: 1,
    type: 'critical',
    icon: AlertTriangle,
    iconColor: 'text-red-500',
    iconBg: 'bg-red-50',
    title: 'Critical interaction detected',
    body: 'Your last analysis flagged a MAJOR interaction between Warfarin and Aspirin.',
    time: '2 hours ago',
    unread: true,
  },
  {
    id: 2,
    type: 'success',
    icon: CheckCircle,
    iconColor: 'text-emerald-500',
    iconBg: 'bg-emerald-50',
    title: 'Analysis complete',
    body: 'Prescription for Ramesh Kumar was analysed successfully. 3 medications verified.',
    time: '5 hours ago',
    unread: true,
  },
  {
    id: 3,
    type: 'info',
    icon: Pill,
    iconColor: 'text-blue-500',
    iconBg: 'bg-blue-50',
    title: 'Generic substitution available',
    body: 'Atorvastatin (brand) can be replaced with a Jan Aushadhi generic — save ₹320/month.',
    time: 'Yesterday',
    unread: false,
  },
  {
    id: 4,
    type: 'info',
    icon: Shield,
    iconColor: 'text-violet-500',
    iconBg: 'bg-violet-50',
    title: 'PMJAY formulary updated',
    body: 'New drugs added to PMJAY coverage list. Your insurance engine has been refreshed.',
    time: '2 days ago',
    unread: false,
  },
  {
    id: 5,
    type: 'info',
    icon: Clock,
    iconColor: 'text-amber-500',
    iconBg: 'bg-amber-50',
    title: 'Prescription expiring soon',
    body: 'The prescription from Dr. S. Mehta dated 22/04 expires in 3 days.',
    time: '3 days ago',
    unread: false,
  },
];

export const NotificationsPage: React.FC = () => {
  const [items, setItems] = React.useState(notifications);

  const markAllRead = () => {
    setItems(prev => prev.map(n => ({ ...n, unread: false })));
  };

  const unreadCount = items.filter(n => n.unread).length;

  return (
    <div className="max-w-2xl">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Notifications</h1>
          <p className="text-sm text-gray-500 mt-1">
            {unreadCount > 0 ? `${unreadCount} unread notification${unreadCount > 1 ? 's' : ''}` : 'All caught up!'}
          </p>
        </div>
        {unreadCount > 0 && (
          <button
            onClick={markAllRead}
            className="text-xs text-violet-600 font-semibold hover:text-violet-700 transition-colors px-3 py-1.5 rounded-lg hover:bg-violet-50"
          >
            Mark all as read
          </button>
        )}
      </div>

      {items.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-14 h-14 bg-gray-100 rounded-2xl flex items-center justify-center mb-4">
            <Bell className="w-7 h-7 text-gray-300" />
          </div>
          <p className="text-sm font-medium text-gray-500">No notifications</p>
          <p className="text-xs text-gray-400 mt-1">You're all caught up.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {items.map(n => {
            const Icon = n.icon;
            return (
              <div
                key={n.id}
                className={`relative flex items-start gap-4 p-4 bg-white rounded-2xl border transition-all duration-150 cursor-pointer hover:shadow-sm ${n.unread ? 'border-violet-100 shadow-sm' : 'border-gray-100'}`}
                onClick={() => setItems(prev => prev.map(i => i.id === n.id ? { ...i, unread: false } : i))}
              >
                {n.unread && (
                  <span className="absolute top-4 right-4 w-2 h-2 rounded-full bg-violet-500" />
                )}
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${n.iconBg}`}>
                  <Icon className={`w-4.5 h-4.5 ${n.iconColor}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-semibold ${n.unread ? 'text-gray-900' : 'text-gray-600'}`}>{n.title}</p>
                  <p className="text-xs text-gray-400 mt-0.5 leading-relaxed">{n.body}</p>
                  <p className="text-[11px] text-gray-300 mt-2">{n.time}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
