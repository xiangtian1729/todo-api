import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { FileQuestion } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
      <FileQuestion className="h-16 w-16 text-muted-foreground" />
      <h1 className="text-2xl font-bold">Page Not Found</h1>
      <p className="text-muted-foreground text-center max-w-md">
        The page you&apos;re looking for doesn&apos;t exist or you don&apos;t have permission to view it.
      </p>
      <Button asChild>
        <Link href="/">Back to Dashboard</Link>
      </Button>
    </div>
  );
}
