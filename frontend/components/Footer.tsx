import Logo from "@/components/Logo";

export default function Footer() {
  return (
    <footer className="mt-16 border-t border-neutral-200 dark:border-neutral-800">
      <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-8 text-sm text-neutral-500 dark:text-neutral-400">
        <p className="flex items-center gap-2 font-serif text-lg font-bold text-neutral-700 dark:text-neutral-200">
          <Logo size={24} />
          Arka <span className="text-brand-600 dark:text-brand-500">News</span>
        </p>
        <p>&copy; {new Date().getFullYear()} Arka News. All rights reserved.</p>
      </div>
    </footer>
  );
}
