import { useI18n } from "../../i18n/I18nProvider";
import type { Attribution, TaxonomyTree } from "../../types";
import type { Deliverable, DeliverablePreview as PreviewModel, LibraryModel } from "./libraryModel";
import DeliverableCard from "./DeliverableCard";

function CardList({
  items,
  taxonomy,
  previewId,
  previews,
  loadingPreviewId,
  previewErrors,
  onPreview,
  onClosePreview,
  onOpen,
  onFiled,
}: {
  items: Deliverable[];
  taxonomy: TaxonomyTree;
  previewId: string | null;
  previews: Record<string, PreviewModel>;
  loadingPreviewId: string | null;
  previewErrors: Set<string>;
  onPreview: (id: string) => void;
  onClosePreview: () => void;
  onOpen: (id: string) => void;
  onFiled: (id: string, attribution: Attribution | null) => void;
}) {
  return (
    <div className="deliverable-grid">
      {items.map((item) => (
        <DeliverableCard
          key={item.id}
          deliverable={item}
          taxonomy={taxonomy}
          preview={previews[item.id] ?? null}
          previewOpen={previewId === item.id}
          previewLoading={loadingPreviewId === item.id}
          previewError={previewErrors.has(item.id)}
          onPreview={onPreview}
          onClosePreview={onClosePreview}
          onOpen={onOpen}
          onFiled={onFiled}
        />
      ))}
    </div>
  );
}

export default function ShelfTree(props: {
  model: LibraryModel;
  taxonomy: TaxonomyTree;
  previewId: string | null;
  previews: Record<string, PreviewModel>;
  loadingPreviewId: string | null;
  previewErrors: Set<string>;
  onPreview: (id: string) => void;
  onClosePreview: () => void;
  onOpen: (id: string) => void;
  onFiled: (id: string, attribution: Attribution | null) => void;
}) {
  const { t } = useI18n();
  return (
    <div className="library-shelves">
      {props.model.shelves.map((client) => (
        <details key={client.client} open className="library-shelf">
          <summary>{client.client}</summary>
          {client.projects.map((project) => (
            <details key={project.project ?? "root"} open className="library-project">
              <summary>{project.project ?? client.client}</summary>
              {project.campaigns.map((campaign) => (
                <section key={campaign.campaign ?? "root"} className="library-campaign">
                  <h3>{campaign.campaign ?? project.project ?? client.client}</h3>
                  <CardList items={campaign.deliverables} {...props} />
                </section>
              ))}
            </details>
          ))}
        </details>
      ))}
      {props.model.unassigned.length > 0 && (
        <section className="library-shelf" aria-label={t("library.shelf.unassigned")}>
          <h2>{t("library.shelf.unassigned")}</h2>
          <CardList items={props.model.unassigned} {...props} />
        </section>
      )}
    </div>
  );
}
