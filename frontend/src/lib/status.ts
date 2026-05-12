export function getStatusColor(status: string, isSelected: boolean = false): string {
  switch (status) {
    case 'success':
      return isSelected ? 'bg-green-50 text-green-800' : 'bg-green-100 text-green-800';
    case 'processing':
      return isSelected ? 'bg-blue-50 text-blue-800' : 'bg-blue-100 text-blue-800';
    case 'error':
      return isSelected ? 'bg-red-50 text-red-800' : 'bg-red-100 text-red-800';
    case 'pending':
    default:
      return isSelected ? 'bg-gray-50 text-gray-800' : 'bg-gray-100 text-gray-700';
  }
}
