import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors",
  {
    variants: {
      variant: {
        default: "border-transparent bg-brand-600 text-white",
        secondary: "border-transparent bg-gray-100 text-gray-800",
        destructive: "border-transparent bg-red-600 text-white",
        outline: "border-gray-300 text-gray-700",
        critical: "border-red-200 bg-red-50 text-red-700",
        high: "border-orange-200 bg-orange-50 text-orange-700",
        medium: "border-amber-200 bg-amber-50 text-amber-700",
        low: "border-green-200 bg-green-50 text-green-700",
        athena: "border-blue-200 bg-blue-50 text-blue-700",
        healthgorilla: "border-purple-200 bg-purple-50 text-purple-700",
        pathway: "border-teal-200 bg-teal-50 text-teal-700",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}
