import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  DndContext,
  closestCenter
} from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
  useSortable,
  arrayMove
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

function SortablePriorityItem({ item, index }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition
  } = useSortable({ id: item.key });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="priority-item"
    >
      <div className="priority-rank">{index + 1}</div>
      <div className="priority-label">{item.label}</div>

      <button
        className="drag-handle"
        {...attributes}
        {...listeners}
      >
        ⋮⋮
      </button>
    </div>
  );
}

function PreferencePage() {
  const navigate = useNavigate();

  const categories = ["전체", "한식", "양식", "일식", "카페"];

  const [selectedCategory, setSelectedCategory] = useState("전체");

  const [priorities, setPriorities] = useState([
    { key: "taste", label: "맛" },
    { key: "price", label: "가격" },
    { key: "mood", label: "분위기" },
    { key: "system", label: "시스템" },
    { key: "service", label: "서비스" }
  ]);

  const handleDragEnd = (event) => {
    const { active, over } = event;

    if (!over || active.id === over.id) return;

    const oldIndex = priorities.findIndex((item) => item.key === active.id);
    const newIndex = priorities.findIndex((item) => item.key === over.id);

    setPriorities((items) => arrayMove(items, oldIndex, newIndex));
  };

  const handleSubmit = () => {
    const priorityKeys = priorities.map((item) => item.key).join(",");
    navigate(`/results?category=${selectedCategory}&priority=${priorityKeys}`);
  };

  return (
    <div className="preference-page">
      <div className="preference-top-bar">
        <input type="text" placeholder="맛집 검색..." />
        <button onClick={() => navigate("/")}>닫기</button>
      </div>

      <section className="preference-section">
        <h2>카테고리</h2>
        <div className="category-list">
          {categories.map((category) => (
            <button
              key={category}
              className={
                selectedCategory === category
                  ? "category-button active"
                  : "category-button"
              }
              onClick={() => setSelectedCategory(category)}
            >
              {category}
            </button>
          ))}
        </div>
      </section>

      <section className="preference-section">
        <h2>평가 기준 우선순위 설정</h2>
        <p>드래그해서 중요 순서를 바꿔보세요</p>

        <DndContext
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext
            items={priorities.map((item) => item.key)}
            strategy={verticalListSortingStrategy}
          >
            <div className="priority-list">
              {priorities.map((item, index) => (
                <SortablePriorityItem
                  key={item.key}
                  item={item}
                  index={index}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>

        <div className="preference-action">
          <button className="result-button" onClick={handleSubmit}>
            추천 결과 보기
          </button>
        </div>
      </section>
    </div>
  );
}

export default PreferencePage;