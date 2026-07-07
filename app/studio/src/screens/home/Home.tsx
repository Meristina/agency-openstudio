import ContextLabel from "./ContextLabel";
import ResumeSection from "./ResumeSection";
import ShortcutsSection from "./ShortcutsSection";
import StartSection from "./StartSection";

export default function Home() {
  return (
    <section className="home-screen">
      <StartSection />
      <ResumeSection />
      <ShortcutsSection />
      <ContextLabel />
    </section>
  );
}
