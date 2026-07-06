import { useI18n } from "../../i18n/I18nProvider";
import type { TaxonomyTree } from "../../types";
import type { ImportedMaterial, ImportModel } from "./importModel";
import MaterialCard from "./MaterialCard";

function CardList({ items, taxonomy, onChanged }: { items: ImportedMaterial[]; taxonomy: TaxonomyTree; onChanged: () => void }) {
  return (
    <div className="deliverable-grid">
      {items.map((item) => <MaterialCard key={`${item.kind}:${item.id}`} item={item} taxonomy={taxonomy} onChanged={onChanged} />)}
    </div>
  );
}

export default function MaterialShelf({ model, taxonomy, onChanged }: { model: ImportModel; taxonomy: TaxonomyTree; onChanged: () => void }) {
  const { t } = useI18n();
  return (
    <div className="library-shelves">
      {model.shelves.map((client) => (
        <details key={client.client} open className="library-shelf">
          <summary>{client.client}</summary>
          {client.projects.map((project) => (
            <details key={project.project ?? "root"} open className="library-project">
              <summary>{project.project ?? client.client}</summary>
              {project.campaigns.map((campaign) => (
                <section key={campaign.campaign ?? "root"} className="library-campaign">
                  <h3>{campaign.campaign ?? project.project ?? client.client}</h3>
                  <CardList items={campaign.items} taxonomy={taxonomy} onChanged={onChanged} />
                </section>
              ))}
            </details>
          ))}
        </details>
      ))}
      {model.unassigned.length > 0 && (
        <section className="library-shelf" aria-label={t("import.shelf.unassigned")}>
          <h2>{t("import.shelf.unassigned")}</h2>
          <CardList items={model.unassigned} taxonomy={taxonomy} onChanged={onChanged} />
        </section>
      )}
    </div>
  );
}
