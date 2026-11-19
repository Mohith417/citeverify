import { useEffect } from "react";
import { Link, Route, Routes, useLocation } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { Landing } from "@/pages/Landing";
import { Upload } from "@/pages/Upload";
import { Analysis } from "@/pages/Analysis";
import { Dashboard } from "@/pages/Dashboard";
import { ClaimDetail } from "@/pages/ClaimDetail";
import { References } from "@/pages/References";
import { Report } from "@/pages/Report";
import { Library } from "@/pages/Library";
import { Method } from "@/pages/Method";
import { Button, EmptyState } from "@/components/ui";

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" as ScrollBehavior });
  }, [pathname]);
  return null;
}

function NotFound() {
  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-24">
      <EmptyState
        title="Page not found"
        description="That page does not exist. Start a verification or open your review history."
        action={
          <Link to="/upload">
            <Button size="sm">Verify a document</Button>
          </Link>
        }
      />
    </div>
  );
}

export default function App() {
  return (
    <>
      <ScrollToTop />
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Landing />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/library" element={<Library />} />
          <Route path="/method" element={<Method />} />
          <Route path="/analysis/:id" element={<Analysis />} />
          <Route path="/documents/:id" element={<Dashboard />} />
          <Route path="/documents/:id/references" element={<References />} />
          <Route path="/documents/:id/report" element={<Report />} />
          <Route path="/documents/:id/claims/:claimId" element={<ClaimDetail />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </>
  );
}
